"""Single-flight background work and UI-safe event delivery."""

from __future__ import annotations

import queue
import threading
from collections.abc import Iterator
from typing import Any, Callable

Event = tuple[str, Any]


class BackgroundRunner:
    """Run one callable on a daemon thread and collect its events."""

    def __init__(self) -> None:
        self._events: queue.Queue[Event] = queue.Queue()

    def emit(self, kind: str, payload: Any = None) -> None:
        self._events.put((kind, payload))

    def report_progress(self, fraction: float, text: str) -> None:
        """Progress callback with the signature expected by the core engine."""
        self.emit("progress", (fraction, text))

    def drain(self) -> Iterator[Event]:
        """Yield every event queued since the previous drain."""
        while True:
            try:
                yield self._events.get_nowait()
            except queue.Empty:
                return

    def submit(self, task: Callable[[], Any]) -> None:
        """Execute *task* off the UI thread; events report completion or failure."""

        def run() -> None:
            try:
                self.emit("done", task())
            except Exception as error:  # noqa: BLE001 - surfaced through the UI
                self.emit("error", str(error) or type(error).__name__)

        threading.Thread(target=run, daemon=True).start()


__all__ = ["BackgroundRunner", "Event"]
