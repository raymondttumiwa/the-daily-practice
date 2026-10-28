"""Verify refresh windows and preservation independently of Garmin connectivity."""
from datetime import date
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from sync_history import health_spans, merge_range


class SyncTests(unittest.TestCase):
    def test_successful_range_replaces_old_values_and_empty_response_clears_only_that_range(self):
        old = [{'calendarDate':'2026-06-01','value':1}, {'calendarDate':'2026-06-02','value':2}]
        fresh = [{'calendarDate':'2026-06-02','value':3}]
        self.assertEqual(merge_range(old, fresh, '2026-06-02', '2026-06-02'), [old[0], fresh[0]])
        self.assertEqual(merge_range(old, [], '2026-06-02', '2026-06-02'), [old[0]])
        self.assertEqual(old[1]['value'], 2)

    def test_refresh_catches_up_after_offline_period_and_retries_old_failure(self):
        old = {'end':'2026-10-10','requests':[{'series':'hrv','start':'2026-06-01','end':'2026-06-07','status':'failed'}]}
        spans = health_spans(old, date(2026,6,1), date(2026,10,29))
        self.assertIn(('hrv','2026-06-01','2026-06-07'), spans)
        covered = set()
        for _, a, b in spans:
            covered.update(range(date.fromisoformat(a).toordinal(),date.fromisoformat(b).toordinal()+1))
        self.assertTrue(set(range(date(2026,10,11).toordinal(),date(2026,10,29).toordinal()+1)) <= covered)
        self.assertNotIn(date(2026,8,1).toordinal(),covered)


if __name__ == '__main__':
    unittest.main()
