from unittest import TestCase
from unittest.mock import Mock, patch

from webtest import TestApp

import ruterstop


class WebAppTestCase(TestCase):
    def setUp(self):
        self.app = TestApp(ruterstop.webapp)
        pass

    def tearDown(self):
        self.app.reset()
        pass

    @patch("ruterstop.get_departures", return_value=None)
    def test_calls_api_on_proper_path(self, mock):
        res = self.app.get("/1234")
        mock.assert_called_once_with(stop_id=1234)

    @patch("ruterstop.get_departures", return_value=None)
    def test_simple_404_error(self, mock):
        res = self.app.get("/", expect_errors=True)
        self.assertEqual(res.content_type, "text/plain")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.body, "Ugyldig stoppested".encode())
        self.assertEqual(mock.call_count, 0)

    @patch("ruterstop.get_departures", return_value=None)
    def test_simple_500_error(self, mock):
        mock.side_effect = Exception("barf")
        res = self.app.get("/1234", expect_errors=True)
        self.assertEqual(res.content_type, "text/plain")
        self.assertEqual(res.status_code, 500)
        self.assertEqual(res.body, "Feil på serveren".encode())
        self.assertEqual(mock.call_count, 1)

    @patch("ruterstop.get_departures", return_value=None)
    def test_calls_api_with_querystring_params(self, mock):
        self.app.get("/1234?direction=inbound&min_eta=5&bogusargs=1337")
        mock.assert_called_once_with(stop_id=1234, directions="inbound",
                                     min_eta=5)
