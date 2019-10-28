#!/usr/bin/env python3
import dateutil.parser
import json
import logging
import math
import re
import socket
import sys
from collections import namedtuple
from datetime import datetime, timedelta

import bottle
import requests

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
    ASCII representation. Other non-ASCII characters are ignored and removed.
    """
    s = re.sub(r"ø", "oe", s, flags=re.IGNORECASE)
    s = re.sub(r"æ", "ae", s, flags=re.IGNORECASE)
    s = re.sub(r"å", "aa", s, flags=re.IGNORECASE)
    return s.encode("ascii", "ignore").decode()


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


def get_departures_func():
    """
    Return a wrapped get_departures function that always returns a list.
    If an API request fails, it will return a cached version of the last
    successful request made, Departures with an 'eta' in the past are removed.
    """
    cache = []
    last_call = None

    def wrapped(*args, **kwargs):
        nonlocal cache
        nonlocal last_call

        # Rate limit upstream API calls
        if not last_call or datetime.now() > (last_call + timedelta(seconds=30)):
            try:
                cache = get_departures(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                logging.error(e)

            last_call = datetime.now()

        return cache

    return wrapped


if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser()

    parser.add_argument('--stop-id', required=True,
        help="find stops at https://stoppested.entur.org (guest:guest)")

    parser.add_argument('--direction', choices=["inbound", "outbound"],
        help="filter direction of departures")

    parser.add_argument('--server', action="store_true",
        help="start a HTTP server")

    parser.add_argument('--host', type=str, default="0.0.0.0",
        help="HTTP server hostname")

    parser.add_argument('--port', type=int, default=4000,
        help="HTTP server listen port")

    parser.add_argument('--debug', action="store_true",
        help="enable debug logging")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    cached_get_departures = get_departures_func()

    if args.server:

        @bottle.route("/")
        def index():
            deps = cached_get_departures(args.stop_id, directions=args.direction)
            return '\n'.join([str(d) for d in deps])

        bottle.run(host=args.host, port=args.port)

    # Otherwise print out stop information and exit
    else:
        deps = cached_get_departures(args.stop_id, directions=args.direction)
        for d in deps:
            print(d)

