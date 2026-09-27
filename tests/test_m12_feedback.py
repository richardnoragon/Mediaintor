import unittest
from unittest.mock import patch
from mediainator.feedback import save_feedback,batch_feedback,batch_counts
from mediainator.installation import identity,window_title

class FeedbackTests(unittest.TestCase):
    def test_partial_save_identifies_verified_book_and_fields(self):
        text=save_feedback('The Time Machine',['tags'],['cover'],{'cover':'permission denied'})
        self.assertIn('The Time Machine',text);self.assertIn('Saved: Tags',text);self.assertIn('Remaining: Cover',text)
        self.assertIn('permission denied',text);self.assertNotIn('Fields changed:',text)
        self.assertIn('No changes to save',save_feedback('Dune'))
    def test_mixed_revert_counts_do_not_double_count_conflicts(self):
        batch={'kind':'revert','items':[dict(state=s,applied={'tags':{}} if s=='failed' else {}) for s in ('complete','failed','conflict','pending','inflight','excluded','discarded')]}
        c=batch_counts(batch);self.assertEqual((c['completed'],c['failed'],c['pending'],c['partial']),(1,1,3,1))
        text=batch_feedback(batch,'interrupted');self.assertIn('Revert interrupted',text);self.assertNotIn('no books changed',text)
        self.assertIn('requiring verification',text)
    def test_preview_cancel_and_completion_are_distinct(self):
        batch={'kind':'revert','items':[dict(state='pending',applied={})]}
        self.assertIn('Confirmation required',batch_feedback(batch));self.assertEqual(batch_feedback(batch,'cancel'),'Cancelled — no books changed.')
        batch['items'][0]['attempt_before']={}
        self.assertNotIn('no books changed',batch_feedback(batch,'cancel'))
        batch['items'][0].update(state='complete',applied={'tags':{'before':['x'],'after':[]}})
        text=batch_feedback(batch);self.assertIn('Revert completed',text);self.assertIn('1 completed',text);self.assertNotIn('Confirmation required',text)
    def test_installation_label_is_not_user_state(self):
        with patch.dict('os.environ',{},clear=True):default=identity()[0]
        with patch.dict('os.environ',{'MEDIAINATOR_INSTALLATION_LABEL':' M12 Test '}):
            self.assertEqual(identity()[0],'M12 Test');self.assertIn('M12 Test',window_title())
        with patch.dict('os.environ',{'MEDIAINATOR_INSTALLATION_LABEL':'bad\nlabel'}):self.assertEqual(identity()[0],default)
        with patch.dict('os.environ',{'MEDIAINATOR_INSTALLATION_LABEL':'x'*81}):self.assertEqual(identity()[0],default)
