import inspect
import json
import os
from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch

import ruterstop


class HumanDeltaTestCase(TestCase):
    def test_output(self):
        ref = datetime.now()
        testcases = [
            (ref - timedelta(seconds=20),  "   naa"),
            (ref + timedelta(seconds=20),  "   naa"),
            (ref + timedelta(minutes=1),   " 1 min"),
            (ref + timedelta(seconds=100), " 1 min"),
            (ref + timedelta(minutes=2),   " 2 min"),
            (ref + timedelta(minutes=10),  "10 min"),
            (ref + timedelta(hours=100),   "99 min")
        ]

        for i, case in enumerate(testcases):
            val, expected = case
            res = ruterstop.human_delta(until=val, since=ref)
            self.assertEqual(res, expected, "test case #%d" % (i + 1))

    def test_default_kwarg_value(self):
        with patch('ruterstop.datetime') as mock_date:
            mock_date.now.return_value = datetime.min
            ruterstop.human_delta(until=datetime.min + timedelta(seconds=120))
            self.assertEqual(mock_date.now.call_count, 1)


class DepartureClassTestCase(TestCase):
    def test_str_representation(self):
        with patch('ruterstop.datetime') as mock_date:
            ref = datetime.min
            mock_date.now.return_value = ref
            in_7_mins = ref + timedelta(minutes=7)
            in_77_mins = ref + timedelta(minutes=77)

            # Test valid representation
            d = ruterstop.Departure(line=21, name="twentyone", eta=in_7_mins, direction="o")
            self.assertEqual(str(d), "21 twentyone    7 min")

            # Test long name trimming
            d = ruterstop.Departure(line=21, name="longname" * 3, eta=in_77_mins, direction="o")
            self.assertEqual(str(d), "21 longnamelon 77 min")


class RuterstopTestCase(TestCase):
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
            res = ruterstop.norwegian_ascii(val)
            self.assertEqual(res, expected, "test case #%d" % (i + 1))

    def test_get_realtime_stop(self):
        with patch('requests.post') as mock:
            ruterstop.get_realtime_stop(stop_id=1337)
            self.assertEqual(mock.call_count, 1)
            _, kwargs = mock.call_args

            self.assertIsNotNone(kwargs["headers"]["ET-Client-Name"])
            self.assertIsNotNone(kwargs["headers"]["ET-Client-Id"])
            self.assertIsNotNone(kwargs.get("timeout"))

    def test_parse_departures(self):
        self.assertTrue(inspect.isgeneratorfunction(ruterstop.parse_departures))

        res = ruterstop.parse_departures(self.raw_departure_data)

        i = 0
        for d in res:
            i += 1
            self.assertIsInstance(d, ruterstop.Departure)
            self.assertIsNotNone(d.line)
            self.assertIsNotNone(d.name)
            self.assertIsNotNone(d.eta)
            self.assertIsNotNone(d.direction)
        self.assertNotEqual(i, 0, "no items were returned")

    def test_timed_cache(self):
        now = MagicMock()
        spy = Mock(return_value=1) # don't need return value

        @ruterstop.timed_cache(expires_sec=60, now=now)
        def func(a, b=None):
            spy() # for counting calls
            return [a, b] # return list to compare references

        def test_set():
            res1 = func(1, 2)
            res2 = func(1, 2)
            self.assertEqual(res1, [1, 2])
            self.assertIs(res1, res2, "did not return same object as first call")
            self.assertEqual(spy.call_count, 1)

            res3 = func(2, 2)
            self.assertEqual(res3, [2, 2])
            self.assertEqual(spy.call_count, 2)


        # Test cache function
        now.return_value = datetime.min
        test_set()
        spy.reset_mock()

        # Test expired key invokes function again
        now.return_value = datetime.min + timedelta(seconds=61)
        test_set()
        spy.reset_mock()
