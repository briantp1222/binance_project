import websocket
import json
import requests
import time
import threading
from typing import List, Dict

class OrderBookClient:
    def __init__(self, symbols: List[str], transaction_fee: float):
        self.__base_uri = "wss://stream.binance.com:9443/ws"
        self.__symbols: List[str] = symbols
        self.__transaction_fee = transaction_fee
        self.__ws = websocket.WebSocketApp(self.__base_uri,
                                           on_message=self.__on_message,
                                           on_error=self.__on_error,
                                           on_close=self.__on_close)
        self.__ws.on_open = self.__on_open
        self.__lookup_snapshot_id: Dict[str, int] = dict()
        self.__lookup_update_id: Dict[str, int] = dict()#store update IDs
        self.__stop_event = threading.Event()
        self.__recent_bids: Dict[str, List[Dict]] = {symbol: [] for symbol in symbols} 
        self.__recent_asks: Dict[str, List[Dict]] = {symbol: [] for symbol in symbols} 

    def __connect(self) -> bool:
        while not self.__stop_event.is_set():
            self.__ws.run_forever()
            time.sleep(1)
        return True

    def __on_message(self, _ws, message):
        data = json.loads(message)
        update_id_low = data.get("U")
        update_id_upp = data.get("u")
        if update_id_low is None:
            return

        symbol = data.get("s")
        snapshot_id = self.__lookup_snapshot_id.get(symbol)
        if snapshot_id is None:
            self.get_snapshot(symbol)
            return
        elif update_id_upp < snapshot_id:
            return

        self.__log_message(message)
        prev_update_id = self.__lookup_update_id.get(symbol)
        if prev_update_id is None:
            assert update_id_low <= snapshot_id <= update_id_upp
        else:
            assert update_id_low == prev_update_id + 1

        self.__lookup_update_id[symbol] = update_id_upp 

        self.update_recent_orders(symbol, data, n=10)
        return

    def __on_error(self, _ws, error):
        print(f"Encountered error: {error}")
        return

    def __on_close(self, _ws, _close_status_code, _close_msg):
        print("Connection closed")
        if not self.__stop_event.is_set():
            print("Reconnecting...")
            time.sleep(1)
            self.__connect()
        return

    def __on_open(self, _ws):
        print("Connection opened")
        for symbol in self.__symbols:
            _ws.send(f"{{\"method\": \"SUBSCRIBE\",  \"params\": [\"{symbol.lower()}@depth\"], \"id\": 1}}")
        return

    def __log_message(self, msg: str) -> None:
        print(msg)
        return

    def get_snapshot(self, symbol: str):
        snapshot_url = f"https://api.binance.com/api/v3/depth?symbol={symbol}&limit=1000"
        x = requests.get(snapshot_url)
        content = x.content.decode("utf-8")
        data = json.loads(content)
        self.__lookup_snapshot_id[symbol] = data["lastUpdateId"] 
        self.__log_message(content)
        self.update_recent_orders(symbol, data, n=10)
        return data

    def start(self) -> bool:
        self.__stop_event.clear()
        threading.Thread(target=self.__connect).start()
        threading.Thread(target=self.__update_snapshot).start()
        return True

    def stop(self) -> bool:
        self.__stop_event.set()
        self.__ws.close()
        return True

    def update_recent_orders(self, symbol: str, data: Dict, n: int = 10) -> None:

        bids = [{'price': float(b[0]), 'quantity': float(b[1])} for b in data.get("b", []) if float(b[1]) > 0]
        asks = [{'price': float(a[0]), 'quantity': float(a[1])} for a in data.get("a", []) if float(a[1]) > 0]
        
        self.__recent_bids[symbol].extend(bids)
        self.__recent_asks[symbol].extend(asks)
        
        self.__recent_bids[symbol] = sorted(self.__recent_bids[symbol], key=lambda x: x['price'], reverse=True)[:n]
        self.__recent_asks[symbol] = sorted(self.__recent_asks[symbol], key=lambda x: x['price'])[:n]

        self.print_recent_orders(symbol)

    def print_recent_orders(self, symbol: str) -> None:
        print(f"Recent Bids for {symbol}:")
        for bid in self.__recent_bids[symbol]:
            print(bid)
        print(f"Recent Asks for {symbol}:")
        for ask in self.__recent_asks[symbol]:
            print(ask)
        if self.__recent_bids[symbol]:
            highest_bid = max((bid for bid in self.__recent_bids[symbol] if bid['quantity'] > 0), key=lambda x: x['price'], default=None)
            if highest_bid:
                print(f"Highest Bid for {symbol}: {highest_bid}")
        if self.__recent_asks[symbol]:
            lowest_ask = min((ask for ask in self.__recent_asks[symbol] if ask['quantity'] > 0), key=lambda x: x['price'], default=None)
            if lowest_ask:
                print(f"Lowest Ask for {symbol}: {lowest_ask}")

                if highest_bid and lowest_ask:
                    bid_ask_spread = highest_bid['price'] - lowest_ask['price']
                    if bid_ask_spread > self.__transaction_fee:
                        print(f"Arbitrage opportunity detected for {symbol}! Spread: {bid_ask_spread}")

    def __update_snapshot(self):
        while not self.__stop_event.is_set():
            for symbol in self.__symbols:
                self.get_snapshot(symbol)
            time.sleep(10) 

def main():
    symbols = ["BTCUSDT", "ETHUSDT"]
    transaction_fee = 0.1 
    orderbook_client = OrderBookClient(symbols, transaction_fee)
    try:
        orderbook_client.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        orderbook_client.stop()
        print("Program stopped by user.")

if __name__ == '__main__':
    main()