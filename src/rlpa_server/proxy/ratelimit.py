import time

class SlidingWindow:
    def __init__(self, limit: int, window: int):
        self.limit = limit
        self.window = window
        self._hits = {}

    def hit(self, key):
        now = time.monotonic()
        ts = [t for t in self._hits.get(key, []) if now - t < self.window]
        if len(ts) >= self.limit:
            self._hits[key] = ts
            return True
        ts.append(now)
        self._hits[key] = ts
        return False
