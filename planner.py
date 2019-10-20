from datetime import datetime, timedelta
import dateutil.parser
import json
import sys
import math
from collections import namedtuple
import socket

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

def human_delta(*, until=None, since=datetime.now()):
    """
    Return string describing minutes left 'until' date occurs.
    Example output:
    < 1 min
      7 min
     10 min
    """
    delta = until.timestamp() - since.timestamp()
    mins = delta / 60
    sign = '<' if mins < 1 else ' '
    return "{}{:2} min".format(sign, math.ceil(mins))


class Departure(namedtuple("Departure", ["line", "name", "eta", "direction"])):
    """Represents a transport departure"""
    def __str__(self):
        return "{line:2} {name:20} {min_left:>7}".format(
            **self._asdict(), min_left=human_delta(until=self.eta))


def get_realtime_stop(*, stop_id=None):
    headers = {
        "Accept": "application/json",
        "ET-Client-Name": "stigok - python-app",
        "ET-Client-Id": "stigok"
    }
    q = ENTUR_GRAPHQL_QUERY % dict(stop_id=stop_id)
    data = dict(query=q, variables={})
    res  = requests.post(ENTUR_GRAPHQL_ENDPOINT, headers=headers, json=data)
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
                name=dep["destinationDisplay"]["frontText"],
                eta=dateutil.parser.parse(dep["expectedArrivalTime"]),
                direction=dep["serviceJourney"]["directionType"]))
    return deps


def get_screen_output(stop_id):
    raw_stop = get_realtime_stop(stop_id=stop_id)
    deps = parse_departures(raw_stop)
    if not deps:
        print("Ingen avganger funnet")
    else:
        for d in deps:
            yield str(d) + '\n'

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--stop-id',
        default="6013", # Stig (Årvoll, Oslo)
        help="Find stops at https://stoppested.entur.org (guest:guest)")
    #parser.add_argument('--retning', choices=[0, 1, 2],
    #    help="begge, innover, utover")
    parser.add_argument('--server', action="store_true",
        help="Start a HTTP server exposing stop data on '/'")
    parser.add_argument('--port', type=int, default=4000,
        help="HTTP server listen port")
    args = parser.parse_args()

    if not args.server:
        print(get_screen_output(args.stop_id))
    if args.server:
        @bottle.route("/")
        def index():
            return """31 Fornebu               20 min
31 Grorud T              30 min
31 Fornebu               50 min
31 Grorud T              60 min
31 Fornebu               80 min
31 Grorud T              90 min
"""
            #return get_screen_output(args.stop_id)

        host = "0.0.0.0"
        bottle.run(host=host, port=args.port)

