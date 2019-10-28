import json
import os
import types
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import ruterstop as api


class PlannelTestCase(unittest.TestCase):
    def setUp(self):
        # Load test data for the external API
        p = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(p, 'test_data.json')) as fp:
            self.raw_departure_data = json.load(fp)

    def test_norwegian_ascii(self):
        testcases = [
            ("Snarøya",              "Snaroeya"),
            ("Ås",                   "aas"),
            ("Ærlig",                "aerlig"),
            ("Voçé não gosta Açaí?", "Vo no gosta Aa?")
        ]

        for i, case in enumerate(testcases):
            val, expected = case
            res = api.norwegian_ascii(val)
            self.assertEqual(res, expected, "test case #%d" % (i + 1))

    def test_human_delta(self):
        ref = datetime.now()
        testcases = [
            (ref - timedelta(seconds=20),  " 0 min"),
            (ref + timedelta(seconds=20),  " 0 min"),
            (ref + timedelta(minutes=1),   " 1 min"),
            (ref + timedelta(seconds=100), " 1 min"),
            (ref + timedelta(minutes=2),   " 2 min"),
            (ref + timedelta(minutes=10),  "10 min"),
            (ref + timedelta(hours=100),   "99 min")
        ]

        for i, case in enumerate(testcases):
            val, expected = case
            res = api.human_delta(until=val, since=ref)
            self.assertEqual(res, expected, "test case #%d" % (i + 1))

    def test_get_realtime_stop(self):
        with patch('requests.post') as mock:
            api.get_realtime_stop(stop_id=1337)
            mock.assert_called_once()
            args, kwargs = mock.call_args

            self.assertIsNotNone(kwargs["headers"]["ET-Client-Name"])
            self.assertIsNotNone(kwargs["headers"]["ET-Client-Id"])
            self.assertIsNotNone(kwargs.get("timeout"))

    def test_parse_departures(self):
        # TODO: use inspect.isgeneratorfunction instead? is that cleaner?
        res = api.parse_departures(self.raw_departure_data)
        self.assertIsInstance(res, types.GeneratorType, "does not return a generator")

        i = 0
        for d in res:
            i += 1
            self.assertIsInstance(d, api.Departure)
            self.assertIsNotNone(d.line)
            self.assertIsNotNone(d.name)
            self.assertIsNotNone(d.eta)
            self.assertIsNotNone(d.direction)
        self.assertNotEqual(i, 0, "no items were returned")

    def test_get_departures(self):
        stop_id = 1337

        with patch('ruterstop.get_realtime_stop') as mock:
            mock.return_value = self.raw_departure_data

            res = api.get_departures(stop_id=stop_id)

            # Assert that it calls on api.get_realtime_stop
            mock.assert_called_once_with(stop_id=stop_id)

            # Assert returns expected types
            self.assertIsInstance(res, list, "does not return a list")
            for d in res:
                self.assertIsInstance(d, api.Departure)

            # Filters on directions
            for direction in ["inbound", "outbound"]:
                res = api.get_departures(stop_id=stop_id, directions=direction)
                for d in res:
                    self.assertIsInstance(d, api.Departure)
                    self.assertEqual(d.direction, direction)

    def test_get_departures_func(self):
        stop_id = 1337

        with patch('ruterstop.get_realtime_stop') as mock:
            mock.return_value = self.raw_departure_data

            # Create the cached function
            fn = api.get_departures_func()
            self.assertIsInstance(fn, types.FunctionType)

            # Assert that immediately subsequent calls are memoized
            # (some sort of cache is implemented)
            res_1 = fn(stop_id=stop_id)
            self.assertIsInstance(res_1, list)
            self.assertIs(res_1, fn(stop_id=stop_id))
            self.assertIs(res_1, fn(stop_id=stop_id))

            # Assert that API is only queried once
            mock.assert_called_once_with(stop_id=stop_id)
