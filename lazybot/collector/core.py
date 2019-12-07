import asyncio
import json
import os
import sys
from typing import NamedTuple

import aioredis
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
    _redis_host = None
    _redis_port = None

    def __init__(self, *args,
                 host=os.getenv('INFLUXDB_HOST', 'localhost'),
                 db=os.getenv('INFLUXDB_DBNAME', 'lazybot'),
                 redis_host=os.getenv('REDIS_HOST', 'localhost'),
                 redis_port=os.getenv('REDIS_PORT', 6379)
                 ):
        for _exchange in args:
            self._exchanges.append(_exchange)
        self._host = host
        self._db = db
        self._redis_host = redis_host
        self._redis_port = redis_port

    async def _write(self, tick):
        try:
            redis = await aioredis.create_pool((self._redis_host, self._redis_port))
            await redis.publish(tick.code, json.dumps(tick))

            async with InfluxDBClient(db=self._db, host=self._host) as db:
                await db.write(tick)
        except Exception as e:
            print(e, file=sys.stderr)

    async def _collect(self, exchange):
        async with exchange.connect() as c:
            while True:
                tick = await c.recv()
                asyncio.ensure_future(self._write(tick))

    def run(self):
        for exchange in self._exchanges:
            asyncio.ensure_future(self._collect(exchange))
        asyncio.get_event_loop().run_forever()


def main():
    LazyBotWorker(BitFlyer).run()
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    main()
