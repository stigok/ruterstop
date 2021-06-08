import inspect
import json
import os
from datetime import datetime, timedelta
from io import StringIO
from unittest import TestCase
from unittest.mock import Mock, MagicMock, patch

from freezegun import freeze_time

import ruterstop


class DepartureClassTestCase(TestCase):
    def test_str_representation(self):
        with patch("ruterstop.utils.datetime") as mock_date:
            ref = datetime.min
            mock_date.now.return_value = ref
            in_7_mins = ref + timedelta(minutes=7)
            in_77_mins = ref + timedelta(minutes=77)

            # Test valid representation
            d = ruterstop.Departure(
                line=21, name="twentyone", eta=in_7_mins, direction="o"
            )
            self.assertEqual(str(d), "21 twentyone    7 min")

            # Test long name trimming
            d = ruterstop.Departure(
                line=21, name="longname" * 3, eta=in_77_mins, direction="o"
            )
            self.assertEqual(str(d), "21 longnamelon 77 min")


class StopPlaceTestCase(TestCase):
    def setUp(self):
        # Load test data for the external API
        p = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(p, "test_stop_data.json")) as fp:
            self.raw_stop_data = json.load(fp)

    def test_get_stop_search_result(self):
        with patch("requests.post") as mock:
            ruterstop.get_stop_search_result(name_search="foobar")
            self.assertEqual(mock.call_count, 1)
            _, kwargs = mock.call_args

            self.assertIsNotNone(kwargs["headers"]["ET-Client-Name"])
            self.assertIsNotNone(kwargs["headers"]["ET-Client-Id"])
            self.assertIsNotNone(kwargs.get("timeout"))

    def test_parse_stop(self):
        stops = ruterstop.parse_stops(self.raw_stop_data)
        for s in stops:
            self.assertTrue(s.id)
            self.assertTrue(s.name)
            self.assertTrue(s.region)
            self.assertTrue(s.parentRegion)


class RuterstopTestCase(TestCase):
    def setUp(self):
        # Load test data for the external API
        p = os.path.realpath(os.path.dirname(__file__))
        with open(os.path.join(p, "test_data.json")) as fp:
            self.raw_departure_data = json.load(fp)

    def test_get_realtime_stop(self):
        with patch("requests.post") as mock:
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

    @patch("ruterstop.get_realtime_stop", return_value=None)
    def test_does_not_hide_realtime_departures_after_eta(self, _):
        now = datetime.now()
        past3min = now - timedelta(minutes=3)
        past2min = now - timedelta(minutes=2)
        past1min = now - timedelta(minutes=1)
        futr1min = now + timedelta(minutes=1, seconds=1)

        deps = []
        d = ruterstop.Departure
        deps.append(d("01", "a", past1min, "inbound", realtime=True))
        deps.append(d("02", "b", past2min, "inbound", realtime=True))
        deps.append(d("03", "c", past3min, "inbound", realtime=True))
        deps.append(d("51", "d", futr1min, "inbound", realtime=True))

        args = " --stop-id=2121 --direction=inbound --grouped".split(" ")

        # Use the fake departure list in this patch
        with patch("ruterstop.parse_departures", return_value=deps) as mock:
            output = StringIO()
            ruterstop.main(args, stdout=output)
            lines = output.getvalue().split("\n")
            output.close()
            self.assertEqual(lines[0], "01, 02, 03        naa")
            self.assertEqual(lines[1], "51 d            1 min")

    @patch("ruterstop.get_realtime_stop", return_value=None)
    def test_groups_output_when_grouped_enabled(self, _):
        now = datetime.now()
        in0min = now + timedelta(seconds=1)
        in1min = now + timedelta(minutes=1)
        in2min = now + timedelta(minutes=2, seconds=1)
        in3min = now + timedelta(minutes=3, seconds=1)
        in4min = now + timedelta(minutes=4, seconds=1)

        # Build list of fake departures
        deps = []
        deps.append(ruterstop.Departure("01", "Zero", in0min, "inbound"))
        deps.append(ruterstop.Departure("10", "Ones", in1min, "inbound"))
        deps.append(ruterstop.Departure("11", "Ones", in1min, "inbound"))
        deps.append(ruterstop.Departure("12", "Ones", in1min, "inbound"))
        deps.append(ruterstop.Departure("20", "Twos", in2min, "inbound"))
        deps.append(ruterstop.Departure("21", "Twos", in2min, "inbound"))
        deps.append(ruterstop.Departure("21", "Thre", in3min, "inbound"))
        deps.append(ruterstop.Departure("21", "Four", in4min, "inbound"))

        # Use the fake departure list in this patch
        with patch("ruterstop.parse_departures", return_value=deps) as mock:
            output = StringIO()
            args = " --stop-id=2121 --direction=inbound --grouped".split(" ")
            ruterstop.main(args, stdout=output)
            lines = output.getvalue().split("\n")
            output.close()
            self.assertEqual(lines[0], "01, 10, 11, 12    naa")
            self.assertEqual(lines[1], "20, 21          2 min")
            self.assertEqual(lines[2], "21 Thre         3 min")
            self.assertEqual(lines[3], "21 Four         4 min")

    @patch("ruterstop.get_realtime_stop", return_value=None)
    def test_shows_timestamp_for_long_etas(self, _):
        seed = datetime(2020, 1, 1, 10, 0, 0)
        with freeze_time(seed):

            def futr(minutes):
                return seed + timedelta(minutes=minutes)

            d = ruterstop.Departure
            deps = [
                # Shouldn't matter if a departure is realtime or not
                d("01", "a", futr(60), "inbound", realtime=True),
                d("02", "b", futr(120), "inbound", realtime=True),
                d("03", "c", futr(150), "inbound", realtime=False),
            ]

            args = " --stop-id=2121 --direction=inbound --long-eta=59".split(" ")

            # Use the fake departure list in this patch
            with patch("ruterstop.parse_departures", return_value=deps) as mock:
                with StringIO() as output:
                    ruterstop.main(args, stdout=output)
                    lines = output.getvalue().split("\n")
                self.assertEqual(lines[0], "01 a            11:00")
                self.assertEqual(lines[1], "02 b            12:00")
                self.assertEqual(lines[2], "03 c            12:30")
