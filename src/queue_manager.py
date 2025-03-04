from typing import List, Dict, Any, Optional, Union
import asyncio


class QueueManager:
    def __init__(self) -> None:
        self.queue: asyncio.Queue = asyncio.Queue()

    @property
    def stats(self) -> Dict[str, Any]:
        return {
            "queue_size": self.queue.qsize(),
            "active_request": self.active_requests,
            "pending_request": self.pending_requests,
            "completed_request": self.completed_requests,
            "failed_request": self.failed_requests,
            "retry_request": self.retry_requests,
        }