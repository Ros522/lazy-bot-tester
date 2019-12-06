import uuid
from backtestlob import BackTestEnv
from collections import deque

import numpy as np


class LazyBackTestEnv:
    def __init__(self, last_timestamp=None):
        self.env = BackTestEnv()
        self.last_timestamp = last_timestamp
        self.queue = deque()

        # tempid -> id
        self.mapper = {}

    @property
    def price(self):
        return self.env.price

    @property
    def side(self):
        return self.env.side

    @property
    def size(self):
        return self.env.size

    @staticmethod
    def _order_to_dict(o):
        return {
            "size": o.size,
            "side": o.side,
            "price": o.price
        }

    def get_orders(self):
        rev = {v: k for k, v in self.mapper.items()}
        return {rev.get(k): self._order_to_dict(v) for k, v in self.env.get_orders().items()}

    def cancel(self, *args, lag=0):

        def _cancel(tempid):
            self.env.cancel(self.mapper[tempid])

        self.queue.append({
            'time': self.last_timestamp + np.timedelta64(lag, 's') if self.last_timestamp is not None else None,
            'method': _cancel,
            'args': args,
        })

    def cancel_all(self, lag=0):
        self.queue.append({
            'time': self.last_timestamp + np.timedelta64(lag, 's') if self.last_timestamp is not None else None,
            'method': self.env.cancel_all
        })

    def entry(self, *args, lag=0):
        temp_id = uuid.uuid4()

        def callback(ret):
            # 注文IDを得た
            self.mapper[temp_id] = ret

        self.queue.append({
            'time': self.last_timestamp + np.timedelta64(lag, 's') if self.last_timestamp is not None else None,
            'method': self.env.entry,
            'args': args,
            'callback': callback
        })

        return temp_id

    def step(self, timestamp, low, high):
        self._lazy_call(timestamp)
        self.last_timestamp = timestamp
        return self.env.step(low, high)

    def step_by_tick(self, timestamp, side, price):
        self._lazy_call(timestamp)
        self.last_timestamp = timestamp
        return self.env.step_by_tick(side, price)

    def _lazy_call(self, now):
        while len(self.queue) > 0:
            left = self.queue.popleft()
            if left['time'] is not None and left['time'] > now:
                self.queue.appendleft(left)
                break
            else:
                if callable(left["method"]):
                    if "args" in left:
                        ret = left["method"](*left["args"])
                        if "callback" in left and callable(left["callback"]):
                            left["callback"](ret)
                    else:
                        left["method"]()
