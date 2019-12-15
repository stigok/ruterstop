import inspect
import json
import os
from datetime import datetime, timedelta
from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch

import ruterstop


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
