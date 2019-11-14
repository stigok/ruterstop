import argparse
import logging
import sys

from ruterstop import get_departures

import bottle


def main(argv=sys.argv, *, stdout=sys.stdout):
    """Main function for CLI usage"""
    # Parse command line arguments
    par = argparse.ArgumentParser()
    par.add_argument('--stop-id',
                     help="find stops at https://stoppested.entur.org (guest:guest)")
    par.add_argument('--direction', choices=["inbound", "outbound"],
                     help="filter direction of departures")
    par.add_argument('--min-eta', type=int, default=0,
                     help="minimum ETA of departures to return")
    par.add_argument('--server', action="store_true",
                     help="start a HTTP server")
    par.add_argument('--host', type=str, default="0.0.0.0",
                     help="HTTP server hostname")
    par.add_argument('--port', type=int, default=4000,
                     help="HTTP server listen port")
    par.add_argument('--debug', action="store_true",
                     help="enable debug logging")

    args = par.parse_args(argv[1:])

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Build direction filter list
    directions = args.direction if args.direction else ["inbound", "outbound"]

    if args.server:
        # Start server
        bottle.run(host=args.host, port=args.port)
    else:
        if not args.stop_id:
            par.error("stop_id is required when not in server mode")
            return

        # Just print stop information
        deps = get_departures(stop_id=args.stop_id, text=False, min_eta=args.min_eta,
                              directions=directions)
        for dep in deps:
            print(dep, file=stdout)
