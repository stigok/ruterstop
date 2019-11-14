#!/usr/bin/env python3
"""
Get realtime stop information for a specific public transport station in Oslo,
Norway. Data is requested from the EnTur JourneyPlanner API.

- API calls are cached to reduce load in `--server` mode
- Use `--help` for usage info.
"""

import logging
import re
import socket
import sys
from collections import namedtuple
from datetime import datetime, timedelta

import requests
import bottle

from utils import timed_cache

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


@timed_cache(expires_sec=60)
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


@bottle.route("/<stop_id:int>")
def get_departures(*, stop_id=None, directions=None, min_eta=0, text=True):
    """
    Returns a filtered list of departures. If `text` is True, return stringified
    departures separated by newlines.

    API calls are cached, so it can be called repeatedly.
    """
    raw_stop = get_realtime_stop(stop_id=stop_id)
    departures = parse_departures(raw_stop)

    # Filter departures with minimum time treshold
    time_treshold = datetime.now() + timedelta(minutes=min_eta)
    directions = ["inbound", "outbound"] if not directions else directions

    for dep in departures:
        if dep.eta >= time_treshold and dep.direction in directions:
            if text:
                yield str(dep) + '\n'
            else:
                yield dep
