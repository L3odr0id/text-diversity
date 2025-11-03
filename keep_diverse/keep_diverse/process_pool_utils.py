import logging
import signal
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager


@contextmanager
def safe_process_pool_executor(max_workers: int):
    original_sigint_handler = signal.signal(signal.SIGINT, signal.SIG_IGN)
    executor = ProcessPoolExecutor(max_workers=max_workers)
    signal.signal(signal.SIGINT, original_sigint_handler)

    try:
        yield executor
    except KeyboardInterrupt:
        logging.info("\nKeyboardInterrupt received, shutting down executor...")
        executor.shutdown(wait=False, cancel_futures=True)
        raise
    else:
        executor.shutdown(wait=True)
