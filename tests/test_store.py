import json
from pathlib import Path
import sqlite3
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import training_store as store
import coach_data
import build_dashboard


class StoreTests(unittest.TestCase):
    def test_migration_is_idempotent_and_preserves_unknown_nutrition(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(store, 'ROOT', Path(tmp)):
            path=Path(tmp)/'data/coach/journal.json';path.parent.mkdir(parents=True)
            meal={'id':'unknown','date':'2026-10-28','food':'Sauce','kcal':None,'protein':None,'carbs':None}
            path.write_text(json.dumps({'meals':[meal],'workouts':[],'checkins':[]}))
            first=store.load_journal();second=store.load_journal()
            self.assertEqual(first,second)
            self.assertEqual(len(first['meals']),1)
            self.assertIsNone(first['meals'][0]['kcal'])
            # After migration, stale JSON must not replace the database.
            path.write_text('{}')
            self.assertEqual(store.load_journal()['meals'],[meal])
            first['meals']=[];store.save_journal(first)
            self.assertEqual(store.load_journal()['meals'],[])
            self.assertEqual(json.loads(path.read_text())['meals'],[])
            self.assertTrue(store.backup().exists())

    def test_repeated_import_has_no_duplicates_and_failed_import_rolls_back(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(store,'ROOT',Path(tmp)):
            root=Path(tmp);history=root/'data/garmin/history.json';history.parent.mkdir(parents=True)
            data={'start':'2026-10-28','end':'2026-10-28','activities':[{'activityId':1,'startTimeLocal':'2026-10-28 18:00:00','duration':60,'activityTrainingLoad':20}], 'sleep':[], 'hrv':[], 'wellness':[]}
            history.write_text(json.dumps(data))
            store.refresh();store.refresh()
            self.assertEqual(len(store.history_bundle()['activities']),1)
            history.write_text('{broken')
            with self.assertRaises(ValueError):store.refresh()
            with store.connection() as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM records WHERE collection='activities'").fetchone()[0],1)

    def test_public_demo_does_not_depend_on_private_inputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'demo.html'
            with patch.object(store,'history_bundle',side_effect=AssertionError('Private data accessed')):
                build_dashboard.build(demo=True,output=path)
            text=path.read_text()
            self.assertIn('"demo": true',text)
            payload=json.loads(re.search(r'<script id="training-data" type="application/json">(.*?)</script>',text,re.S)[1])
            self.assertTrue(payload.get('demo'))
            self.assertTrue(all(m['id'].startswith('demo-') for m in payload['coach']['journal']['meals']))
            self.assertNotIn('GARMIN_PERSONAL_API_KEY=',text)
            self.assertNotIn('/Users/',text)


if __name__=='__main__':unittest.main()
