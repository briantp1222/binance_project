import unittest
from src.order_book_client import OrderBookClient

class TestOrderBookClient(unittest.TestCase):
    def test_get_snapshot(self):
        client = OrderBookClient(['BTCUSDT'], 'https://api.binance.com')
        bids, asks = client.get_snapshot('BTCUSDT')
        self.assertTrue(bids.shape[1] == 2)
        self.assertTrue(asks.shape[1] == 2)

if __name__ == '__main__':
    unittest.main()