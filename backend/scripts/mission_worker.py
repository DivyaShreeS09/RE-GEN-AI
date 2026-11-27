"""Execute only investigations delegated by authenticated facility staff."""
import logging
import os
import signal
import sys
from pathlib import Path
from threading import Event

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.execution_queue import next_job
from core.recovery import execute_investigation
from core.schema import require_schema


def main():
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("Worker requires an explicit shared application database.")
    require_schema()
    stop = Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    while not stop.is_set():
        try:
            job = next_job()
            if job:
                execute_investigation(*job)
                continue
        except Exception:
            logging.warning("Investigation interrupted; retained committed checkpoints.")
        stop.wait(2)


if __name__ == "__main__":
    main()
