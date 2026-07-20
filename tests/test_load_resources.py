import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

PATH=Path(__file__).parents[1]/'load-tests'/'sales_load.py'
SPEC=importlib.util.spec_from_file_location('sales_load',PATH)
sales_load=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(sales_load)

class ResourceMeasurementTests(unittest.TestCase):
    def test_memory_unit_conversion(self):
        self.assertEqual(sales_load.memory_mb('512MiB'),512)
        self.assertEqual(sales_load.memory_mb('1GiB'),1024)
        self.assertAlmostEqual(sales_load.memory_mb('1024KiB'),1)
    def test_explicit_process_sampling(self):
        sampler=sales_load.ResourceSampler([os.getpid()])
        with patch.object(sales_load.subprocess,'run',return_value=Mock(stdout='12.5 20480')):
            cpu,memory=sampler._process_sample()
        self.assertEqual(cpu,12.5); self.assertEqual(memory,20)
        self.assertEqual(sampler.source,'processes')

if __name__=='__main__': unittest.main()
