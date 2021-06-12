#!/usr/bin/env python3
"""
Get realtime stop information for a specific public transport station in Oslo,
Norway. Data is requested from the EnTur JourneyPlanner API.

- API calls are cached to reduce load in `--server` mode
- Use `--help` for usage info.
"""

import argparse
import logging
import os
import socket
import sys
from collections import defaultdict, namedtuple
from datetime import datetime, timedelta

import requests
import bottle

from ruterstop.utils import delta, human_delta, norwegian_ascii, timed_cache

__version__ = "0.5.0"

# Default settings
DEFAULTS = dict(long_eta=59)

ENTUR_CLIENT_ID = __version__
ENTUR_STOP_PLACE_ENDPOINT = "https://api.entur.io/stop-places/v1/graphql"
ENTUR_STOP_PLACE_QUERY = """
{
  stopPlace(size: 250, query: "%(stop_name)s") {
    id
    topographicPlace {
      name {
        value
      }
      parentTopographicPlace {
        name {
          value
        }
      }
    }
    name {
      value
    }
  }
}
"""
ENTUR_GRAPHQL_ENDPOINT = "https://api.entur.io/journey-planner/v2/graphql"
ENTUR_GRAPHQL_QUERY = """
{
  stopPlace(id: "NSR:StopPlace:%(stop_id)s") {
    name
    estimatedCalls(timeRange: 72100, numberOfDepartures: 20) {
      expectedArrivalTime
      realtime
      destinationDisplay {
        frontText
      }
      serviceJourney {
        directionType
        line {
          publicCode
        }
      }
    }
  }
}
"""

webapp = bottle.Bottle()
log = logging.getLogger("ruterstop")


def not_found_error_handler(res):
    res.set_header("Content-Type", "text/plain")
    return "Ugyldig stoppested"


webapp.error(code=404)(not_found_error_handler)


def default_error_handler(res):
    res.set_header("Content-Type", "text/plain")
    log.error(res.traceback)
    return "Feil på serveren"


webapp.default_error_handler = default_error_handler


class Departure(
    namedtuple("Departure", ["line", "name", "eta", "direction", "realtime"])
):
    """Represents a transport departure"""

    def __str__(self):
        name = str(self.line)
        if self.name:
            name += " " + self.name
        return "{:14}{:>7}".format(name[:14], human_delta(until=self.eta))

    def ts_str(self):
        name = str(self.line)
        if self.name:
            name += " " + self.name
        return "{:16}{:%H:%M}".format(name[:14], self.eta)


# Python < 3.7 equivalent of `defaults` kwarg of `namedtuple`
Departure.__new__.__defaults__ = (False,)


@timed_cache(expires_sec=30)
def get_realtime_stop(*, stop_id=None):
    """
    Query EnTur API for realtime stop information.

    See output format and build your own queries at:
    https://api.entur.io/journey-planner/v2/ide/
    """
    log.debug("Requesting fresh data from API")
    headers = {
        "Accept": "application/json",
        "ET-Client-Name": "ruterstop - stigok/ruterstop",
        "ET-Client-Id": ENTUR_CLIENT_ID,
    }
    qry = ENTUR_GRAPHQL_QUERY % dict(stop_id=stop_id)
    res = requests.post(
        ENTUR_GRAPHQL_ENDPOINT,
        headers=headers,
        timeout=5,
        json=dict(query=qry, variables={}),
    )
    res.raise_for_status()
    return res.json()


class StopPlace(namedtuple("StopPlace", ["id", "name", "region", "parentRegion"])):
    def __str__(self):
        return "{id:8s}{name} ({region}, {parentRegion})".format(**self._asdict())


def get_stop_search_result(*, name_search):
    log.debug("Searching for stop by name: %s", name_search)
    headers = {
        "Accept": "application/json",
        "ET-Client-Name": "ruterstop - stigok/ruterstop",
        "ET-Client-Id": ENTUR_CLIENT_ID,
    }
    qry = ENTUR_STOP_PLACE_QUERY % dict(stop_name=name_search)
    res = requests.post(
        ENTUR_STOP_PLACE_ENDPOINT,
        headers=headers,
        timeout=5,
        json=dict(query=qry, variables={}),
    )
    res.raise_for_status()
    return res.json()


def parse_stops(raw_dict):
    for stop in raw_dict["data"]["stopPlace"]:
        numid = stop["id"].rsplit(":", maxsplit=1).pop()
        yield StopPlace(
            numid,
            stop["name"]["value"],
            stop["topographicPlace"]["name"]["value"],
            stop["topographicPlace"]["parentTopographicPlace"]["name"]["value"],
        )


def parse_departures(raw_dict, *, date_fmt="%Y-%m-%dT%H:%M:%S%z"):
    """
    Parse a JSON response dict from EnTur JourneyPlanner API and
    return a list of Departure objects.

    Parsing relies on date format being exactly as specified in date_fmt.

    Date is stored as time-zone unaware to avoid relying on a date parsing
    library to handle time-zones.
    """
    if raw_dict["data"]["stopPlace"]:
        for dep in raw_dict["data"]["stopPlace"]["estimatedCalls"]:
            eta = datetime.strptime(dep["expectedArrivalTime"], date_fmt).replace(
                tzinfo=None
            )
            yield Departure(
                line=dep["serviceJourney"]["line"]["publicCode"],
                name=norwegian_ascii(dep["destinationDisplay"]["frontText"]),
                eta=eta,
                direction=dep["serviceJourney"]["directionType"],
                realtime=dep["realtime"],
            )


@webapp.route("/<stop_id:int>")
def serve_departures(stop_id):
    """
    Responds to web requests by turning whitelisted querystring values into
    kwargs passed on to format_departure_list.
    """
    q = bottle.request.query
    kw = dict()

    if q.direction:
        kw["directions"] = q.direction
    if q.min_eta:
        kw["min_eta"] = int(q.min_eta)
    if q.grouped:
        kw["grouped"] = True
    if q.long_eta:
        kw["long_eta"] = int(q.long_eta)

    deps = get_departures(stop_id=stop_id)
    bottle.response.set_header("Content-Type", "text/plain")
    return format_departure_list(deps, **kw)


def get_departures(*, stop_id=None):
    """
    Returns a list of Departure objects.

    Upstream API calls are cached, so it can be called repeatedly.
    """
    raw_stop = get_realtime_stop(stop_id=stop_id)
    return parse_departures(raw_stop)


def format_departure_list(
    departures,
    *,
    min_eta=0,
    long_eta=DEFAULTS["long_eta"],
    directions=None,
    grouped=False
):
    """
    Filters, formats and groups departures based on arguments passed.
    """
    deps = (d for d in departures)

    # Filter on directions
    dirs = ["inbound", "outbound"] if not directions else directions
    deps = filter(lambda d: d.direction in dirs, deps)

    # Filter departures with minimum time treshold
    time_treshold = datetime.now() + timedelta(minutes=min_eta)
    deps = filter(
        lambda d: d.eta >= time_treshold or (min_eta == 0 and d.realtime), deps
    )

    # Group departures with same departure time
    # TODO: The check for whether directions has filter might need more work
    if grouped and dirs:
        # Group by ETA value
        by_eta = defaultdict(list)
        for dep in deps:
            by_eta[human_delta(dep.eta)].append(dep)

        # Build string output
        newdeps = list()
        for _, deps in by_eta.items():
            # Print single departures normally
            if len(deps) == 1:
                newdeps.append(deps[0])
                continue

            newdeps.append(
                Departure(
                    line=", ".join([d.line for d in deps]),
                    name="",
                    eta=deps[0].eta,
                    direction=deps[0].direction,
                )
            )
        deps = newdeps

    # Create pretty output
    s = ""
    for dep in deps:
        if 0 < long_eta < delta(dep.eta):
            s += dep.ts_str() + "\n"
        else:
            s += str(dep) + "\n"
    return s


def main(argv=sys.argv, *, stdout=sys.stdout):
    """Main function for CLI usage"""
    # Parse command line arguments
    par = argparse.ArgumentParser(prog="ruterstop")
    par.add_argument(
        "--search-stop", type=str, metavar="<name>", help="search for a stop by name"
    )
    par.add_argument(
        "--stop-id",
        metavar="<id>",
        help="use --search-stop or official website to find stops https://stoppested.entur.org (guest:guest)",
    )
    par.add_argument(
        "--direction",
        choices=["inbound", "outbound"],
        help="filter direction of departures",
    )
    par.add_argument(
        "--min-eta",
        type=int,
        default=0,
        metavar="<minutes>",
        help="minimum ETA of departures to return",
    )
    par.add_argument(
        "--long-eta",
        type=int,
        default=DEFAULTS["long_eta"],
        metavar="<minutes>",
        help="show departure time when ETA is later than this limit (disable with -1)",
    )
    par.add_argument(
        "--grouped",
        action="store_true",
        help="group departures with same ETA together when --direction is also specified.",
    )
    par.add_argument("--server", action="store_true", help="start a HTTP server")
    par.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        metavar="<ip|hostname>",
        help="HTTP server hostname",
    )
    par.add_argument(
        "--port",
        type=int,
        default=4000,
        metavar="<port>",
        help="HTTP server listen port",
    )
    par.add_argument("--debug", action="store_true", help="enable debug logging")
    par.add_argument("--version", action="store_true", help="show version information")

    args = par.parse_args(argv[1:])

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Show version information?
    if args.version:
        print("ruterstop " + __version__, file=stdout)
        return

    # Search for stop?
    if args.search_stop:
        result = get_stop_search_result(name_search=args.search_stop)
        stops = parse_stops(result)
        for s in stops:
            print(s, file=stdout)
        return

    # Build direction filter list
    directions = args.direction if args.direction else ["inbound", "outbound"]

    if args.server:
        # Start server
        bottle.run(webapp, host=args.host, port=args.port)
    else:
        if not args.stop_id:
            par.error("stop_id is required when not in server mode")
            return

        # Just print stop information
        deps = get_departures(stop_id=args.stop_id)
        formatted = format_departure_list(
            deps,
            min_eta=args.min_eta,
            long_eta=args.long_eta,
            directions=directions,
            grouped=args.grouped,
        )

        print(formatted, file=stdout)


if __name__ == "__main__":
    main()
