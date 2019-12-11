"""
Note for webtest and bottle:
Even though I'd ideally want to mock ruterstop.get_departures, that function
is decorated with @bottle.get() on import-time, consequently wrapping the
underlying function before it is patched/mocked.
A work-around for this is to mock get_realtime_stop instead, as it is the
first function called in get_departures, and use that to e.g. raise Exceptions
as a side-effect.
"""
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

    # The patchability of this module isn't great for this kind of test
    @patch('ruterstop.get_realtime_stop', return_value={"data": "foobar"})
    @patch('ruterstop.parse_departures', returl_value=[])
    def test_calls_api_on_proper_path(self, parse_departures, get_realtime_stop):
        res = self.app.get('/1234')
        get_realtime_stop.assert_called_once_with(stop_id=1234)

    def test_simple_404_error(self):
        res = self.app.get('/', expect_errors=True)
        self.assertEqual(res.content_type, 'text/plain')
        self.assertEqual(res.status_code, 404)
        self.assertTrue(str(res.body).count('\n') <= 1) # a single line of text
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
