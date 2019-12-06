import asyncio
from typing import NamedTuple
from aioinflux import *

from lazybot.collector.exchanges.bitflyer import BitFlyer


@lineprotocol
class Tick(NamedTuple):
    timestamp: TIMEINT
    code: TAG
    side: TAG
    price: FLOAT
    size: FLOAT
    latency: FLOAT


class LazyBotWorker:
    _exchanges = []
    _host = None
    _db = None

    def __init__(self, *args, host='localhost', db='lazybot'):
        for _exchange in args:
            self._exchanges.append(_exchange)
        self._host = host
        self._db = db

    async def _write(self, tick):
        try:
            async with InfluxDBClient(db=self._db, host=self._host) as db:
                await db.write(tick)
        except Exception as e:
            print(e)

    async def _collect(self, exchange):
        async with exchange.connect() as c:
            while True:
                tick = await c.recv()
                asyncio.ensure_future(self._write(tick))

    def run(self):
        for exchange in self._exchanges:
            asyncio.ensure_future(self._collect(exchange))
        asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    LazyBotWorker(BitFlyer).run()
    asyncio.get_event_loop().run_forever()
