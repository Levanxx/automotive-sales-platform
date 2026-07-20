import unittest

from scripts.validate_n8n import REQUIRED, validate_all

class N8nWorkflowTests(unittest.TestCase):
    def test_all_required_cloud_workflows_are_valid(self):
        self.assertEqual(set(REQUIRED),{
            'inactive-prospect-alert.json','service-sync.json',
            'service-health-monitor.json','workflow-error-handler.json'})
        self.assertEqual(validate_all(),{})

if __name__=='__main__': unittest.main()
