import time

class RateLimiter:
    def __init__(self, calls, period):
        self.calls = calls
        self.period = period
        self.requests = 0
        self.start_time = time.time()

    def wait(self):
        """Pause execution if the rate limit is exceeded."""
        current_time = time.time()
        elapsed_time = current_time - self.start_time

        if self.requests >= self.calls:
            if elapsed_time < self.period:
                time.sleep(self.period - elapsed_time)
            self.start_time = time.time()
            self.requests = 0

        self.requests += 1