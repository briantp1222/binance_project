import time

class RateLimiter:
    def __init__(self, calls, period):
        self.calls = calls
        self.period = period
        self.requests = 0
        self.start_time = time.time()

    def wait(self):
        """Pause execution if the rate limit is exceeded."""
        current_time = time.time()
        elapsed_time = current_time - self.start_time

        if self.requests >= self.calls:
            if elapsed_time < self.period:
                time.sleep(self.period - elapsed_time)
            self.start_time = time.time()
            self.requests = 0

        self.requests += 1
        
import numpy as np
import pyopencl as cl

class GPUProcessing:
    def __init__(self):
        self.context, self.queue = self.setup_opencl()

    def setup_opencl(self):
        platform = cl.get_platforms()[0]
        device = platform.get_devices()[0]
        context = cl.Context([device])
        queue = cl.CommandQueue(context)
        return context, queue

    def parallel_process(self, data):
        mf = cl.mem_flags
        data = np.array(data, dtype=np.float32)  # Ensure all data is float32
        data_buf = cl.Buffer(self.context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=data)
        output_buf = cl.Buffer(self.context, mf.WRITE_ONLY, data.nbytes)
        prg = cl.Program(self.context, '''
        __kernel void double_data(__global const float *data, __global float *output) {
            int i = get_global_id(0);
            output[i] = data[i] * 2;
        }
        ''').build()
        prg.double_data(self.queue, data.shape, None, data_buf, output_buf)
        result = np.empty_like(data)
        cl.enqueue_copy(self.queue, result, output_buf).wait()
        return result
    
import requests
import pandas as pd

class OrderBookClient:
    def __init__(self, symbols, api_url, rate_limiter, gpu_processor):
        self.symbols = symbols
        self.api_url = api_url
        self.rate_limiter = rate_limiter
        self.gpu_processor = gpu_processor

    def get_snapshot(self, symbol):
        self.rate_limiter.wait()
        url = f"{self.api_url}/api/v3/depth?symbol={symbol}&limit=1000"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            self.validate_data(data, symbol) 
            return data
        else:
            raise Exception(f"API request failed with status {response.status_code}: {response.text}")

    def validate_data(self, data, symbol):
        if 'bids' not in data or 'asks' not in data:
            raise ValueError(f"Missing 'bids' or 'asks' in data for {symbol}")
        if not data['bids'] or not data['asks']:
            raise ValueError(f"Empty 'bids' or 'asks' for {symbol}")

    def store_data(self, data, symbol):
        bids = pd.DataFrame(data['bids'], columns=['price', 'quantity'])
        asks = pd.DataFrame(data['asks'], columns=['price', 'quantity'])
        bids.to_csv(f'{symbol}_bids.csv', index=False)
        asks.to_csv(f'{symbol}_asks.csv', index=False)

    def parallel_process_data(self, data):
        print(f"Starting parallel processing for {data['symbol']}")
        bids = np.array(data['bids'], dtype=float)[:, 0]  # Assumes bids are [price, volume]
        asks = np.array(data['asks'], dtype=float)[:, 0]  # Assumes asks are [price, volume]
        
        processed_bids = self.gpu_processor.parallel_process(bids)
        processed_asks = self.gpu_processor.parallel_process(asks)
        
        print("Parallel processing completed.")
        print("Processed Bids:", processed_bids)
        print("Processed Asks:", processed_asks)
        return processed_bids, processed_asks

import unittest

from unittest.mock import patch, MagicMock


class TestOrderBookClient(unittest.TestCase):
    def setUp(self):
        self.rate_limiter = RateLimiter(10, 60)
        self.gpu_processor = GPUProcessing()
        self.client = OrderBookClient(['BTCUSDT'], 'https://api.binance.com', self.rate_limiter, self.gpu_processor)

    @patch('requests.get')
    def test_get_snapshot(self, mock_get):
        # Setup mock response from requests.get
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'bids': [['5000.0', '1.0'], ['4990.0', '2.0']],
            'asks': [['5010.0', '1.5'], ['5020.0', '1.2']]
        }
        mock_get.return_value = mock_response

        # Call the method
        result = self.client.get_snapshot('BTCUSDT')

        # Check if requests.get was called correctly
        mock_get.assert_called_once_with('https://api.binance.com/api/v3/depth?symbol=BTCUSDT&limit=1000')

        # Verify the response is correctly processed
        self.assertEqual(result, mock_response.json.return_value)

        # Verify validate_data was called correctly
        with patch.object(self.client, 'validate_data') as mock_validate:
            self.client.get_snapshot('BTCUSDT')
            mock_validate.assert_called_once_with(mock_response.json.return_value, 'BTCUSDT')

if __name__ == '__main__':
    unittest.main()
             