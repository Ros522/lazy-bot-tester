import asyncio
import json
from datetime import datetime

import numpy as np
import websockets


class BitFlyer:
    def __init__(self, tag="BITFLYERFX", channel='lightning_executions_FX_BTC_JPY', retry=1, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.tag = tag
        self.channel = channel
        self.task = None
        self.retry = retry
        self.queue = asyncio.Queue()

    async def __aenter__(self):
        self.task = asyncio.ensure_future(self.run())
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.task.cancel()

    async def run(self):
        while True:
            try:
                async with websockets.connect('wss://ws.lightstream.bitflyer.com/json-rpc') as ws:
                    await ws.send(json.dumps({"method": "subscribe", "params": {"channel": self.channel}}))
                    while True:
                        data = await ws.recv()
                        self.on_message(json.loads(data))
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(e)
                # retry after 1 sec
                await asyncio.sleep(self.retry)

    async def recv(self):
        return await self.queue.get()

    def on_message(self, message):
        from lazybot.collector.core import Tick

        if message['method'] == "channelMessage":
            tick = message['params']['message']
            now = np.datetime64(datetime.utcnow())

            # 同一タイムスタンプごとに集計
            _agged_tick = {}
            for t in tick:
                timestamp = np.datetime64(t["exec_date"])
                _agged_tick[timestamp] = {
                    "timestamp": timestamp,
                    "side": t["side"],
                    "price": t["price"],
                    "size": _agged_tick[timestamp]["size"] + t["size"] if timestamp in _agged_tick else t["size"]
                }
            for item in _agged_tick.values():
                latency = (now - item["timestamp"]).astype(np.int64) / 1000000000
                self.queue.put_nowait(
                    Tick(timestamp=item["timestamp"].astype('datetime64[ns]').astype('int'),
                         code=self.tag,
                         side=item["side"],
                         price=item["price"],
                         size=item["size"],
                         latency=latency
                         )
                )

    @classmethod
    def connect(cls, **kwargs):
        return cls(**kwargs)
