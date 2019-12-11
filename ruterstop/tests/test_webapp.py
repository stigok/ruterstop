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
from unittest.mock import patch

from webtest import TestApp

import ruterstop



class WebAppTestCase(TestCase):
    def setUp(self):
        self.app = TestApp(ruterstop.webapp)
        pass

    def tearDown(self):
        self.app.reset()
        pass

    def test_simple_404_error(self):
        res = self.app.get('/', expect_errors=True)
        self.assertEqual(res.content_type, 'text/plain')
        self.assertEqual(res.status_code, 404)
        self.assertTrue(str(res.body).count('\n') <= 1) # a single line of text
        self.assertEqual(res.body, "Ugyldig stoppested".encode())

    def test_simple_500_error(self):
        with patch('ruterstop.get_realtime_stop') as mock:
            mock.side_effect = Exception("Trigger a 500")

            res = self.app.get('/1234', expect_errors=True)
            mock.assert_called_once()

            self.assertEqual(res.content_type, 'text/plain')
            self.assertEqual(res.status_code, 500)
            self.assertTrue(str(res.body).count('\n') <= 1) # a single line of text
            self.assertEqual(res.body, "Feil på serveren".encode())
