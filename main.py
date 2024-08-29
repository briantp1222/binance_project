
from src.order_book_client import OrderBookClient

def main():
    symbols = ['BTCUSDT', 'ETHUSDT']
    api_url = 'https://api.binance.com'
    client = OrderBookClient(symbols, api_url)
    for symbol in symbols:
        processed_bids, processed_asks = client.process_data(symbol)
        print(f"Processed Bids for {symbol}: {processed_bids}")
        print(f"Processed Asks for {symbol}: {processed_asks}")

if __name__ == '__main__':
    main()
