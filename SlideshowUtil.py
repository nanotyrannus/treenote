from concurrent.futures import ThreadPoolExecutor
import multiprocessing

class ImageWriter:
    _pool = None

    def __init__(self):
        if self._pool is None:
            self._pool = ThreadPoolExecutor(max_workers=2)

    def pool(self):
        return self._pool