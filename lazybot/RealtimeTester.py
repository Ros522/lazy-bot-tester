from datetime import datetime
from typing import NamedTuple

from aioinflux import *

from lazybot.env import LazyBackTestEnv


@lineprotocol
class Result(NamedTuple):
    timestamp: TIMEINT
    code: TAG
    pnl: FLOAT
    trade: FLOAT


class RealtimeTester:

    def __init__(self, code=datetime.now().strftime('%Y%m%d-%H%M%S'), host='localhost', db='lazybot'):
        self.env = LazyBackTestEnv()
        self.pnl = 0
        self.trade = 0
        self.code = code
        self._host = host
        self._db = db

    def get_orders(self):
        return self.env.get_orders()

    def cancel(self, *args, lag=0):
        return self.env.cancel(*args, lag=lag)

    def cancel_all(self, lag=0):
        return self.env.cancel_all(lag=lag)

    def entry(self, *args, lag=0):
        return self.env.entry(*args, lag=lag)

    def step_by_tick(self, timestamp, side, price):
        pnl, trade = self.env.step_by_tick(timestamp, side, price)

        self.pnl += pnl
        self.trade += trade

        # Write
        self._write(Result(timestamp=timestamp, code=self.code, pnl=self.pnl, trade=self.trade))

    async def _write(self, data):
        try:
            async with InfluxDBClient(db=self._db, host=self._host) as db:
                await db.write(data)
        except Exception as e:
            print(e)
