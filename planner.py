from datetime import datetime, timedelta
import dateutil.parser
import json
import re
import sys
import math
from collections import namedtuple
import socket
import functools
import logging

import requests
import bottle

ENTUR_CLIENT_ID = socket.gethostname()
ENTUR_GRAPHQL_ENDPOINT = "https://api.entur.io/journey-planner/v2/graphql"
ENTUR_GRAPHQL_QUERY = """
{
  stopPlace(id: "NSR:StopPlace:%(stop_id)s") {
    id
    name
    estimatedCalls(timeRange: 72100, numberOfDepartures: 10) {
      realtime
      expectedArrivalTime
      destinationDisplay {
        frontText
      }
      serviceJourney {
        directionType
        id
        line {
          id
          publicCode
        }
      }
    }
  }
}
"""

def norwegian_ascii(s):
    """
    Returns an ASCII string with Norwegian chars replaced with their closest
    visual character. Other characters ignored and removed.
    """
    s = re.sub(r"ø", "oe", s, flags=re.IGNORECASE)
    s = re.sub(r"æ", "ae", s, flags=re.IGNORECASE)
    s = re.sub(r"å", "aa", s, flags=re.IGNORECASE)
    return s


def human_delta(until=None, *, since=None):
    """
    Return a 7 char long string describing minutes left 'until' date occurs.
    Example output:
    < 1 min
      7 min
     10 min
     99 min
    """
    if not since:
        since = datetime.now()
    delta = until.timestamp() - since.timestamp()
    mins = min(delta / 60, 99) # no more than two digits long
    sign = '<' if mins < 1 else ' '
    return "{}{:2} min".format(sign, math.ceil(mins))


class Departure(namedtuple("Departure", ["line", "name", "eta", "direction"])):
    """Represents a transport departure"""
    def __str__(self):
        return "{:2} {:10} {:>7}".format(
            self.line, self.name[:10], human_delta(until=self.eta))


@functools.lru_cache(maxsize=1)
def get_realtime_stop(*, stop_id=None, cache_token=None):
    """
    Query EnTur API for realtime stop information.
    Use a cache_token to memoize calls.

    See output format and build your own queries at:
    https://api.entur.io/journey-planner/v2/ide/
    """
    logging.debug("Requesting fresh data from API")
    headers = {
        "Accept": "application/json",
        "ET-Client-Name": "stigok - python-app",
        "ET-Client-Id": ENTUR_CLIENT_ID
    }
    q = ENTUR_GRAPHQL_QUERY % dict(stop_id=stop_id)
    data = dict(query=q, variables={})
    res  = requests.post(ENTUR_GRAPHQL_ENDPOINT, headers=headers, json=data, timeout=5)
    res.raise_for_status()
    return res.json()


def parse_departures(raw_dict):
    """
    Parses a response dict from EnTur JourneyPlanner API and
    returns a list of Departure objects.
    """
    deps = []
    if raw_dict["data"]["stopPlace"]:
        for dep in raw_dict["data"]["stopPlace"]["estimatedCalls"]:
            deps.append(Departure(
                line=dep["serviceJourney"]["line"]["publicCode"],
                name=norwegian_ascii(dep["destinationDisplay"]["frontText"]),
                eta=dateutil.parser.parse(dep["expectedArrivalTime"]),
                direction=dep["serviceJourney"]["directionType"]))
    return deps


def get_departures(stop_id, *, directions=None, cache_token=None):
    """
    Get a list of departures for a particular stop. Use a cache token for
    memoization of the last call to EnTur API.
    Use directions param to return items only going in a specific direction.
    """
    try:
        raw_stop = get_realtime_stop(stop_id=stop_id, cache_token=cache_token)
        departures = parse_departures(raw_stop)
    except requests.exceptions.Timeout as e:
        logging.error("API call timed out")
        logging.debug(e)
        departures = []

    if not directions:
        directions = ["inbound", "outbound"]
    elif not isinstance(directions, list):
        directions = [directions]

    return [d for d in departures if d.direction in directions]


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('--stop-id',
        default="6013", # Stig (Årvoll, Oslo)
        help="Find stops at https://stoppested.entur.org (guest:guest)")

    parser.add_argument('--direction', choices=["inbound", "outbound"],
        help="Filter direction of departures")

    parser.add_argument('--server', action="store_true",
        help="Start a HTTP server exposing stop data on '/'")

    parser.add_argument('--host', type=str, default="0.0.0.0",
        help="HTTP server hostname")

    parser.add_argument('--port', type=int, default=4000,
        help="HTTP server listen port")

    args = parser.parse_args()

    # Print out stop information
    if not args.server:
        deps = get_departures(args.stop_id, directions=args.direction)
        for d in deps:
            print(d)

    # Start HTTP Server
    if args.server:
        # Define main route
        @bottle.route("/")
        def index():
            # This will give a fresh response every minute
            token = datetime.now().strftime("%Y%m%d%H%M")
            deps = get_departures(args.stop_id, directions=args.direction, cache_token=token)
            return '\n'.join([str(d) for d in deps])

        bottle.run(host=args.host, port=args.port)

