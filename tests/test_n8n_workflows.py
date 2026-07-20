import io
import unittest
from unittest.mock import patch

from scripts.validate_n8n import REQUIRED, validate_all
from scripts.n8n_cloud_smoke_check import request_json

class N8nWorkflowTests(unittest.TestCase):
    def test_all_required_cloud_workflows_are_valid(self):
        self.assertEqual(set(REQUIRED),{
            'inactive-prospect-alert.json','service-sync.json',
            'service-health-monitor.json','workflow-error-handler.json'})
        self.assertEqual(validate_all(),{})
    def test_smoke_request_sends_automation_headers(self):
        response=io.BytesIO(b'{"status":"ok"}'); response.status=200
        with patch('scripts.n8n_cloud_smoke_check.urlopen',return_value=response) as mocked:
            status,data=request_json('https://api.example.com/health',key='secret',extra_headers={'X-Inactivity-Days':'3'})
        request=mocked.call_args.args[0]
        self.assertEqual(status,200); self.assertEqual(data['status'],'ok')
        self.assertEqual(request.get_header('X-automation-key'),'secret')
        self.assertEqual(request.get_header('X-inactivity-days'),'3')

if __name__=='__main__': unittest.main()
