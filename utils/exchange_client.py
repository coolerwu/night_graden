"""交易所客户端 / Exchange Client (Mock + Live via ccxt)"""

from __future__ import annotations

import random
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional

from models.market_data import Kline, TickerSnapshot, OrderBookSnapshot
from models.order import Order, OrderSide, OrderType, OrderStatus
from utils.logger import get_logger

logger = get_logger("exchange_client")


class BaseExchangeClient(ABC):
    """交易所客户端基类 / Base exchange client interface"""

    @abstractmethod
    def fetch_klines(
        self, symbol: str, timeframe: str, limit: int = 100
    ) -> list[Kline]:
        ...

    @abstractmethod
    def fetch_ticker(self, symbol: str) -> TickerSnapshot:
        ...

    @abstractmethod
    def fetch_order_book(self, symbol: str, limit: int = 10) -> OrderBookSnapshot:
        ...

    @abstractmethod
    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
    ) -> Order:
        ...

    @abstractmethod
    def cancel_order(self, order_id: str, symbol: str) -> bool:
        ...

    @abstractmethod
    def fetch_balance(self) -> dict:
        ...


class MockExchangeClient(BaseExchangeClient):
    """模拟交易所 / Mock exchange for backtesting and development"""

    def __init__(self, initial_balance: float = 10000.0):
        self._balance = {"USDT": initial_balance, "BTC": 0.0}
        self._base_price = 50000.0
        self._orders: list[Order] = []
        logger.info("MockExchangeClient initialized with %.2f USDT", initial_balance)

    def fetch_klines(
        self, symbol: str, timeframe: str, limit: int = 100
    ) -> list[Kline]:
        klines = []
        now = datetime.utcnow()
        price = self._base_price
        for i in range(limit):
            change = random.uniform(-0.02, 0.02)
            o = price
            c = price * (1 + change)
            h = max(o, c) * (1 + random.uniform(0, 0.01))
            l = min(o, c) * (1 - random.uniform(0, 0.01))  # noqa: E741
            vol = random.uniform(100, 1000)
            klines.append(
                Kline(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp=now - timedelta(hours=limit - i),
                    open=round(o, 2),
                    high=round(h, 2),
                    low=round(l, 2),
                    close=round(c, 2),
                    volume=round(vol, 4),
                )
            )
            price = c
        self._base_price = price
        return klines

    def fetch_ticker(self, symbol: str) -> TickerSnapshot:
        price = self._base_price * (1 + random.uniform(-0.005, 0.005))
        spread = price * 0.001
        return TickerSnapshot(
            symbol=symbol,
            last_price=round(price, 2),
            bid=round(price - spread / 2, 2),
            ask=round(price + spread / 2, 2),
            volume_24h=round(random.uniform(5000, 50000), 2),
            change_pct_24h=round(random.uniform(-5, 5), 2),
        )

    def fetch_order_book(self, symbol: str, limit: int = 10) -> OrderBookSnapshot:
        price = self._base_price
        bids = [
            [round(price - i * price * 0.001, 2), round(random.uniform(0.1, 2), 4)]
            for i in range(limit)
        ]
        asks = [
            [round(price + i * price * 0.001, 2), round(random.uniform(0.1, 2), 4)]
            for i in range(limit)
        ]
        return OrderBookSnapshot(symbol=symbol, bids=bids, asks=asks)

    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
    ) -> Order:
        fill_price = price or self._base_price
        # Check balance
        if side == OrderSide.BUY:
            cost = fill_price * quantity
            if self._balance.get("USDT", 0) < cost:
                return Order(
                    id=str(uuid.uuid4())[:8],
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    price=fill_price,
                    quantity=quantity,
                    status=OrderStatus.FAILED,
                    strategy_name="",
                )
            self._balance["USDT"] -= cost
            self._balance["BTC"] = self._balance.get("BTC", 0) + quantity
        else:
            if self._balance.get("BTC", 0) < quantity:
                return Order(
                    id=str(uuid.uuid4())[:8],
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    price=fill_price,
                    quantity=quantity,
                    status=OrderStatus.FAILED,
                    strategy_name="",
                )
            self._balance["BTC"] -= quantity
            self._balance["USDT"] += fill_price * quantity

        order = Order(
            id=str(uuid.uuid4())[:8],
            symbol=symbol,
            side=side,
            order_type=order_type,
            price=fill_price,
            quantity=quantity,
            filled_quantity=quantity,
            filled_price=fill_price,
            status=OrderStatus.FILLED,
        )
        self._orders.append(order)
        logger.info("Mock order filled: %s %s %.6f @ %.2f", side.value, symbol, quantity, fill_price)
        return order

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        logger.info("Mock cancel order: %s", order_id)
        return True

    def fetch_balance(self) -> dict:
        return dict(self._balance)


class LiveExchangeClient(BaseExchangeClient):
    """实盘交易所客户端 / Live exchange client via ccxt"""

    def __init__(
        self,
        exchange_name: str,
        api_key: str,
        secret: str,
        password: str = "",
    ):
        import ccxt

        exchange_class = getattr(ccxt, exchange_name, None)
        if exchange_class is None:
            raise ValueError(f"Unsupported exchange: {exchange_name}")

        config = {"apiKey": api_key, "secret": secret, "enableRateLimit": True}
        if password:
            config["password"] = password

        self._exchange = exchange_class(config)
        logger.info("LiveExchangeClient connected to %s", exchange_name)

    def fetch_klines(
        self, symbol: str, timeframe: str, limit: int = 100
    ) -> list[Kline]:
        ohlcv = self._exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        return [
            Kline(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=datetime.utcfromtimestamp(row[0] / 1000),
                open=row[1],
                high=row[2],
                low=row[3],
                close=row[4],
                volume=row[5],
            )
            for row in ohlcv
        ]

    def fetch_ticker(self, symbol: str) -> TickerSnapshot:
        t = self._exchange.fetch_ticker(symbol)
        return TickerSnapshot(
            symbol=symbol,
            last_price=t["last"],
            bid=t.get("bid", t["last"]),
            ask=t.get("ask", t["last"]),
            volume_24h=t.get("quoteVolume", 0),
            change_pct_24h=t.get("percentage", 0),
        )

    def fetch_order_book(self, symbol: str, limit: int = 10) -> OrderBookSnapshot:
        ob = self._exchange.fetch_order_book(symbol, limit)
        return OrderBookSnapshot(
            symbol=symbol,
            bids=ob["bids"][:limit],
            asks=ob["asks"][:limit],
        )

    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
    ) -> Order:
        if order_type == OrderType.MARKET:
            result = self._exchange.create_market_order(symbol, side.value, quantity)
        else:
            result = self._exchange.create_limit_order(
                symbol, side.value, quantity, price
            )

        return Order(
            id=result["id"],
            symbol=symbol,
            side=side,
            order_type=order_type,
            price=result.get("price", 0) or 0,
            quantity=quantity,
            filled_quantity=result.get("filled", 0) or 0,
            filled_price=result.get("average", 0) or 0,
            status=OrderStatus.FILLED
            if result.get("status") == "closed"
            else OrderStatus.PENDING,
        )

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        self._exchange.cancel_order(order_id, symbol)
        return True

    def fetch_balance(self) -> dict:
        bal = self._exchange.fetch_balance()
        return {k: v for k, v in bal.get("free", {}).items() if v and v > 0}


def create_exchange_client(
    mode: str = "mock",
    exchange_name: str = "binance",
    api_key: str = "",
    secret: str = "",
    password: str = "",
    initial_balance: float = 10000.0,
) -> BaseExchangeClient:
    """工厂函数：根据模式创建对应的交易所客户端"""
    if mode == "live":
        return LiveExchangeClient(exchange_name, api_key, secret, password)
    return MockExchangeClient(initial_balance)
