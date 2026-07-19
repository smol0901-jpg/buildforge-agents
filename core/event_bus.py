from __future__ import annotations
from collections import defaultdict
import threading

class EventBus:
    def __init__(self):
        self._subs = defaultdict(list)
        self._lock = threading.Lock()
        self.history = []
    def on(self, event, cb):
        with self._lock: self._subs[event].append(cb)
    def off(self, event, cb):
        with self._lock:
            if cb in self._subs[event]: self._subs[event].remove(cb)
    def emit(self, event, payload=None):
        data = {"event": event, **(payload or {})}
        with self._lock:
            self.history.append(data)
            if len(self.history) > 2000: self.history = self.history[-1000:]
            subs = list(self._subs.get(event, [])) + list(self._subs.get("*", []))
        for cb in subs:
            try: cb(data)
            except Exception: pass

BUS = EventBus()
