import unittest
import numpy as np
from src.gpu_processing import GPUProcessing

class TestGPUProcessing(unittest.TestCase):
    def test_parallel_processing(self):
        gpu_processor = GPUProcessing()
        data = np.array([1.0, 2.0, 3.0], dtype=float)
        processed_data = gpu_processor.parallel_processing(data)
        self.assertTrue(np.array_equal(processed_data, [2.0, 4.0, 6.0]))

if __name__ == '__main__':
    unittest.main()