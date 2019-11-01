#!/usr/bin/env python3
"""
Get realtime stop information for a specific public transport station in Oslo,
Norway. Data is requested from the EnTur JourneyPlanner API.

- API calls are memoized to reduce load in `--server` mode
- Use `--help` for usage info.
"""

import functools
import logging
import math
import re
import socket
from collections import namedtuple
from datetime import datetime, timedelta
import dateutil.parser

import requests
import bottle

ENTUR_CLIENT_ID = socket.gethostname()
ENTUR_GRAPHQL_ENDPOINT = "https://api.entur.io/journey-planner/v2/graphql"
ENTUR_GRAPHQL_QUERY = """
{
  stopPlace(id: "NSR:StopPlace:%(stop_id)s") {
    name
    estimatedCalls(timeRange: 72100, numberOfDepartures: 10) {
      realtime
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
     1 min
     7 min
    10 min
    99 min
    """
    if not since:
        since = datetime.now()

    if until <= since:
        mins = 0
    else:
        secs = (until - since).seconds
        mins = math.floor(secs / 60)
        mins = min(mins, 99) # no more than two digits long

    return "{:2} min".format(mins)


class Departure(namedtuple("Departure", ["line", "name", "eta", "direction"])):
    """Represents a transport departure"""
    def __str__(self):
        return "{:2} {:10} {:>7}".format(
            self.line, self.name[:10], human_delta(until=self.eta))


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


def parse_departures(raw_dict):
    """
    Parse a JSON response dict from EnTur JourneyPlanner API and
    return a list of Departure objects.
    """
    if raw_dict["data"]["stopPlace"]:
        for dep in raw_dict["data"]["stopPlace"]["estimatedCalls"]:
            yield Departure(
                line=dep["serviceJourney"]["line"]["publicCode"],
                name=norwegian_ascii(dep["destinationDisplay"]["frontText"]),
                eta=dateutil.parser.parse(dep["expectedArrivalTime"], ignoretz=True),
                direction=dep["serviceJourney"]["directionType"]
            )


# TODO: This function does not bring a lot to the table. Rename or remove?
# TODO: Make this a generator function instead? Since parse_departures does it.
def get_departures(stop_id, *, directions=None):
    """
    Return a list of departures for a particular stop.
    Use directions param to return items only going in a specific direction.
    """
    raw_stop = get_realtime_stop(stop_id=stop_id)
    departures = parse_departures(raw_stop)

    # Build direction filter list
    if not directions:
        directions = ["inbound", "outbound"]
    elif not isinstance(directions, list):
        directions = [directions]

    return [d for d in departures if d.direction in directions]


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
            key = functools._make_key(_args, _kwargs, False)

            if key not in cache or time > cache[key]["timestamp"] + expires_sec:
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

    @timed_cache(expires_sec=60)
    def cached_get_departures(stop_id, directions):
        for dep in get_departures(stop_id=stop_id, directions=directions):
            yield dep

    if args.server:

        @bottle.route("/")
        def _():
            deps = cached_get_departures(args.stop_id, directions=args.direction)
            return '\n'.join([str(d) for d in deps])

        bottle.run(host=args.host, port=args.port)

    # Otherwise print out stop information and exit
    else:
        deps = cached_get_departures(args.stop_id, directions=args.direction)
        for item in deps:
            print(item)

if __name__ == "__main__":
    main()
