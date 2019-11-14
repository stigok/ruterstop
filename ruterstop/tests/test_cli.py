import inspect
import json
import os
from freezegun import freeze_time
from datetime import datetime, timedelta
from io import StringIO

import unittest
from unittest.mock import Mock, MagicMock, patch

import ruterstop
from ruterstop import main

def run(args):
    out = StringIO()
    ruterstop.main.main(['TEST'] + args, stdout=out)
    lines = out.getvalue().split('\n')
    return lines

class CommandLineInterfaceTestCase(unittest.TestCase):
    def setUp(self):
        self.patches = []

        p = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(p, 'test_data.json')) as fp:
            departure_data = json.load(fp)
            patcher = patch('ruterstop.get_realtime_stop', return_value=departure_data)
            self.patches.append(patcher)
            self.patched_get_realtime_stop = patcher.start()

            # Get the time of the first departure to use as reference for tests
            first_departure = list(ruterstop.parse_departures(departure_data))[0]
            self.first_departure_time = first_departure.eta

        # This is highly dependent on the test data
        self.expected_output = [
            "31 Snaroeya       naa",
            "25 Majorstuen     naa",
            "25 Loerenskog     naa",
            "31 Grorud T     5 min",
            "31 Tonsenhagen  5 min",
            "31 Fornebu      6 min",
            "31 Grorud T    11 min",
            "31 Snaroeya    12 min",
            "25 Loerenskog  14 min",
            "25 Majorstuen  15 min"
        ]

    def tearDown(self):
        for p in self.patches:
            p.stop()

    def test_simple_output(self):
        with freeze_time(self.first_departure_time):
            # Call CLI with custom args
            out = run(["--stop-id", "1337"])
            self.patched_get_realtime_stop.assert_called_once_with(stop_id="1337")

            actual = filter(None, out) # remove empty lines
            self.assertEqual(list(actual), self.expected_output)

    def test_adjustable_minimum_time(self):
        with freeze_time(self.first_departure_time):
            # Call CLI with custom args
            out = run(["--stop-id", "1337", "--min-eta", "2"])
            lines = filter(None, out) # remove empty lines
            self.assertEqual(list(lines), self.expected_output[3:]) # skip first 3

    def test_direction_arg_is_accounted_for(self):
        with freeze_time(self.first_departure_time):
            out = run(["--stop-id", "1337", "--direction", "outbound"])
            self.assertNotIn("Tonsenhagen", out)

            out = run(["--stop-id", "1337", "--direction", "inbound"])
            self.assertNotIn("Majorstuen", out)