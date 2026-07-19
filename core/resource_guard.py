from __future__ import annotations
import time, threading
try: import psutil
except ImportError: psutil = None

class ResourceGuard:
    def __init__(self, critical=98.0, recover=97.0, enabled=True):
        self.critical, self.recover, self.enabled = critical, recover, enabled
        self._last = 0.0; self._lock = threading.Lock()
    def sample(self):
        if not psutil: return 0.0
        val = psutil.virtual_memory().percent
        with self._lock: self._last = val
        return val
    @property
    def last(self):
        with self._lock: return self._last
    def wait_if_critical(self, timeout=30.0):
        if not self.enabled or not psutil: return
        start = time.time()
        while self.sample() >= self.critical:
            if time.time() - start > timeout: break
            time.sleep(0.5)
    def breath(self, seconds=0.3):
        if not self.enabled: return
        self.wait_if_critical()
        if self.sample() >= self.recover: time.sleep(seconds)
