import tempfile,unittest
from pathlib import Path
from copy import deepcopy
from unittest.mock import Mock,patch
from PyQt6.QtWidgets import QApplication,QPushButton
from mediainator.bulk_dialog import BulkDialog
from mediainator.bulk import plan
from tests.test_bulk import record
from mediainator.activity import ActivityStore,ActivityBridge
from mediainator.activity_panel import ActivityPanel,ActivityDetails

APP=QApplication.instance() or QApplication([])

class M13WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.dialog=BulkDialog(self.root/'library',self.root/'bulk',[])
        self.addCleanup(self.dialog.close)
        self.response=dict(library_uuid='library-uuid',records={'book-uuid':record()},errors={})

    def batch(self):
        return plan(self.dialog.store,[dict(book=1,uuid='book-uuid')],self.response,'Add Tags',dict(tags=['New']))

    def test_tabs_keep_result_separate_and_preview_pins_target(self):
        d=self.dialog;b=self.batch();d.batch=b;d.render()
        self.assertEqual(d.tabs.tabText(0),'New Bulk Edit')
        self.assertEqual(d.tabs.tabText(1),'Batch History')
        self.assertFalse(d.history.isEnabled());self.assertFalse(d.tabs.isTabEnabled(1))
        d.change_view(1);self.assertIs(d.batch,b)
        d.back();d.tabs.setCurrentIndex(1);self.assertEqual(d.view_index,1)
        self.assertIsNone(d.batch);self.assertEqual(d.table.rowCount(),0)

    def test_completed_execution_selects_its_own_journal(self):
        d=self.dialog;old=self.batch();old['items'][0]['state']='discarded';d.store.save(old);d.refresh_history()
        d.tabs.setCurrentIndex(1);d.tabs.setCurrentIndex(0)
        b=self.batch();d.batch=b;d.render()
        def request(**kwargs):
            result=deepcopy(kwargs['batch']);result['items'][0]['state']='complete';result['items'][0]['applied']={'tags':{'before':['Classic'],'after':['Classic','New']}};d.store.save(result);return result
        with patch.object(d,'request',side_effect=request):d.execute()
        self.assertEqual(d.history.currentData(),b['id'])
        self.assertIn('Completed',d.windowTitle());self.assertFalse(d.confirm.isEnabled())
        d.tabs.setCurrentIndex(1)
        self.assertEqual(d.batch['id'],b['id'])
        self.assertEqual(d.history.currentData(),b['id'])
        d.tabs.setCurrentIndex(0);self.assertEqual(d.batch['id'],b['id'])

    def test_missing_selected_history_never_targets_other_record(self):
        d=self.dialog;a=self.batch();a['items'][0]['state']='discarded';d.store.save(a)
        b=self.batch();b['items'][0]['state']='discarded';d.store.save(b)
        d.refresh_history(preferred=a['id']);d.store.delete(a);d.refresh_history()
        self.assertIsNone(d.history.currentData());self.assertIsNone(d.selected_history())
        self.assertTrue(all(not button.isEnabled() for button in d.history_actions))

    def test_bidirectional_links_are_read_only(self):
        d=self.dialog;a=self.batch();a['items'][0]['state']='complete';d.store.save(a)
        b=self.batch();b.update(kind='revert',original=a['id'],operation='Revert Add Tags');b['items'][0]['state']='complete';d.store.save(b)
        d.refresh_history(preferred=b['id']);d.tabs.setCurrentIndex(1)
        d.describe_history();before={p.name:p.read_bytes() for p in d.store.folder.glob('*.json')}
        self.assertEqual(d.links.currentData(),a['id']);d.navigate_related()
        self.assertEqual(d.history.currentData(),a['id']);self.assertEqual(d.links.currentData(),b['id'])
        d.navigate_related();self.assertEqual(d.history.currentData(),b['id'])
        self.assertEqual(before,{p.name:p.read_bytes() for p in d.store.folder.glob('*.json')})

    def test_revert_completion_selects_new_revert_and_preserves_original(self):
        d=self.dialog;a=self.batch();a['items'][0]['state']='complete';d.store.save(a)
        d.refresh_history(preferred=a['id']);d.tabs.setCurrentIndex(1)
        b=self.batch();b.update(kind='revert',operation='Revert Add Tags',original=a['id'])
        d.batch=b;d.render();before=(d.store.folder/(a['id']+'.json')).read_bytes()
        def request(**kwargs):
            result=deepcopy(kwargs['batch']);result['items'][0]['state']='complete';d.store.save(result);return result
        with patch.object(d,'request',side_effect=request):d.execute()
        self.assertEqual(d.history.currentData(),b['id']);self.assertIn('Revert — Completed',d.windowTitle())
        self.assertEqual(d.links.currentData(),a['id'])
        self.assertEqual(before,(d.store.folder/(a['id']+'.json')).read_bytes())

    def test_partial_and_late_stop_results_never_claim_false_completion(self):
        d=self.dialog;b=self.batch();d.batch=b;d.render()
        def interrupted(**kwargs):
            d.stop_requested=True;result=deepcopy(kwargs['batch']);d.store.save(result);return result
        with patch.object(d,'request',side_effect=interrupted):d.execute()
        self.assertIn('Interrupted',d.windowTitle());self.assertFalse(d.confirm.isEnabled())
        d.back();d.batch=b;d.render()
        def finished(**kwargs):
            d.stop_requested=True;result=deepcopy(kwargs['batch']);result['items'][0]['state']='complete';d.store.save(result);return result
        with patch.object(d,'request',side_effect=finished):d.execute()
        self.assertIn('Completed',d.windowTitle());self.assertNotIn('Interrupted',d.windowTitle())

    def test_contextual_recovery_actions_dispatch_without_implicit_save(self):
        store=ActivityStore(self.root/'activity','person','device');bridge=ActivityBridge(store,lambda m:None)
        bridge.record('Single-book recovery','one',outcome='success',pending=True,recovery=True,source={'kind':'recovery'})
        panel=ActivityPanel(bridge);panel.controller=Mock();self.addCleanup(panel.close)
        dialog=ActivityDetails(store.records()[0],panel);self.addCleanup(dialog.close)
        self.assertEqual(dialog.actions['review'].text(),'Open recovery draft')
        self.assertEqual(dialog.actions['discard'].text(),'Discard preserved draft')
        dialog.actions['review'].click();panel.controller.perform.assert_called_once_with('review',store.records()[0]['id'])
        panel.show_history();history=panel.history;self.addCleanup(history.close)
        history.tree.setCurrentItem(history.tree.topLevelItem(0));self.assertFalse(history.details_button.isEnabled())
        history.tree.setCurrentItem(history.tree.topLevelItem(0).child(0));self.assertTrue(history.details_button.isEnabled())
        self.assertIn('Close history',[b.text() for b in history.findChildren(QPushButton)])

    def test_resolved_recovery_guidance_matches_disabled_review(self):
        store=ActivityStore(self.root/'activity','person','device');bridge=ActivityBridge(store,lambda m:None)
        bridge.record('Single-book recovery','resolved',outcome='success',pending=False,recovery=False,source={'kind':'recovery'})
        panel=ActivityPanel(bridge);panel.controller=Mock();self.addCleanup(panel.close)
        dialog=ActivityDetails(store.records()[0],panel);self.addCleanup(dialog.close)
        self.assertFalse(dialog.actions['review'].isEnabled())
        self.assertIn('Recovery is resolved',dialog.content.toPlainText())
        self.assertNotIn('Choose Open recovery draft',dialog.content.toPlainText())
