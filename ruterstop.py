#!/usr/bin/env python3
"""
Get realtime stop information for a specific public transport station in Oslo,
Norway. Data is requested from the EnTur JourneyPlanner API.

- API calls are cached to reduce load in `--server` mode
- Use `--help` for usage info.
"""

import functools
import logging
import re
import socket
from collections import namedtuple
from datetime import datetime, timedelta

import requests
import bottle

ENTUR_CLIENT_ID = socket.gethostname()
ENTUR_GRAPHQL_ENDPOINT = "https://api.entur.io/journey-planner/v2/graphql"
ENTUR_GRAPHQL_QUERY = """
{
  stopPlace(id: "NSR:StopPlace:%(stop_id)s") {
    name
    estimatedCalls(timeRange: 72100, numberOfDepartures: 10) {
      expectedArrivalTime
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

def norwegian_ascii(unicode_str):
    """
    Returns an ASCII string with Norwegian chars replaced with their closest
    ASCII representation. Other non-ASCII characters are ignored and removed.
    """
    unicode_str = re.sub(r"ø", "oe", unicode_str, flags=re.IGNORECASE)
    unicode_str = re.sub(r"æ", "ae", unicode_str, flags=re.IGNORECASE)
    unicode_str = re.sub(r"å", "aa", unicode_str, flags=re.IGNORECASE)
    return unicode_str.encode("ascii", "ignore").decode()


def human_delta(until=None, *, since=None):
    """
    Return a 6 char long string describing minutes left 'until' date occurs.
    Example output:
       naa (if delta < 60 seconds)
     1 min
     7 min
    10 min
    99 min
    """
    now_str = "{:>6}".format("naa")
    if not since:
        since = datetime.now()

    if since > until:
        return now_str

    secs = (until - since).seconds
    mins = int(secs / 60) # floor
    mins = max(0, min(mins, 99)) # between 0 and 99

    if mins < 1:
        return now_str

    return "{:2} min".format(mins)


class Departure(namedtuple("Departure", ["line", "name", "eta", "direction"])):
    """Represents a transport departure"""
    def __str__(self):
        return "{:2} {:11}{:>7}".format(
            self.line, self.name[:11], human_delta(until=self.eta))


def get_realtime_stop(*, stop_id=None):
    """
    Query EnTur API for realtime stop information.

    See output format and build your own queries at:
    https://api.entur.io/journey-planner/v2/ide/
    """
    logging.debug("Requesting fresh data from API")
    headers = {
        "Accept": "application/json",
        "ET-Client-Name": "ruterstop - stigok/ruterstop",
        "ET-Client-Id": ENTUR_CLIENT_ID
    }
    qry = ENTUR_GRAPHQL_QUERY % dict(stop_id=stop_id)
    res = requests.post(ENTUR_GRAPHQL_ENDPOINT, headers=headers, timeout=5,
                        json=dict(query=qry, variables={}))
    res.raise_for_status()
    return res.json()


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
            eta = datetime.strptime(dep["expectedArrivalTime"],
                                    date_fmt).replace(tzinfo=None)
            yield Departure(
                line=dep["serviceJourney"]["line"]["publicCode"],
                name=norwegian_ascii(dep["destinationDisplay"]["frontText"]),
                eta=eta,
                direction=dep["serviceJourney"]["directionType"]
            )


def timed_cache(*, expires_sec=60, now=datetime.now):
    """
    Decorator function to cache function calls with same arguments for a set
    amount of time.

    It does not delete any keys from the cache, so it might grow indefinitely.
    """
    cache = {}

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*_args, **_kwargs):
            time = now()
            key = functools._make_key(_args, _kwargs, False) # pylint: disable=protected-access

            if key not in cache or time > cache[key]["timestamp"] + timedelta(seconds=expires_sec):
                cache[key] = dict(value=func(*_args, **_kwargs), timestamp=time)

            return cache[key]["value"]

        return wrapper

    return decorator


def main():
    """Main function for CLI usage"""
    # Parse command line arguments
    import argparse
    par = argparse.ArgumentParser()
    par.add_argument('--stop-id', required=True,
                     help="find stops at https://stoppested.entur.org (guest:guest)")
    par.add_argument('--direction', choices=["inbound", "outbound"],
                     help="filter direction of departures")
    par.add_argument('--server', action="store_true",
                     help="start a HTTP server")
    par.add_argument('--host', type=str, default="0.0.0.0",
                     help="HTTP server hostname")
    par.add_argument('--port', type=int, default=4000,
                     help="HTTP server listen port")
    par.add_argument('--debug', action="store_true",
                     help="enable debug logging")

    args = par.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Create a cached function
    get_cached_realtime_stop = timed_cache(expires_sec=60)(get_realtime_stop)

    # Build direction filter list
    if not args.direction:
        directions = ["inbound", "outbound"]
    else:
        directions = [args.direction]

    if args.server:
        @bottle.route("/")
        def _():
            raw_stop = get_cached_realtime_stop(stop_id=args.stop_id)
            deps = parse_departures(raw_stop)
            return '\n'.join([str(d) for d in deps if d.direction in directions])

        bottle.run(host=args.host, port=args.port)

    # Otherwise print out stop information and exit
    else:
        raw_stop = get_cached_realtime_stop(stop_id=args.stop_id)
        for dep in parse_departures(raw_stop):
            print(dep)


if __name__ == "__main__":
    main()
