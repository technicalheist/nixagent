from typing import List, Dict, Any, Optional, Callable
from .logger import logger


class ContextWindowManager:
    """
    Manages the agent's message list to prevent context window exhaustion.

    Strategy:
        - Sliding window: Always keeps the system message and the last N messages.
        - Summarization: Optionally calls a summarizer callable on the evicted
          messages and inserts the summary as a system-level context note.

    Usage:
        manager = ContextWindowManager(max_messages=20, summarizer=my_fn)
        messages = manager.maybe_trim(messages)
    """

    def __init__(
        self,
        max_messages: int = 50,
        summarizer: Optional[Callable[[List[Dict]], str]] = None,
    ):
        """
        Args:
            max_messages:  Maximum number of messages (excluding the system
                           prompt) to keep in context. When exceeded, older
                           messages are evicted. Must be >= 4.
            summarizer:    Optional callable that receives the evicted message
                           list and returns a summary string. The summary is
                           injected as a ``user`` role message right after the
                           system prompt so the agent retains historical context.
        """
        if max_messages < 4:
            raise ValueError("max_messages must be at least 4 to maintain a meaningful context.")
        self.max_messages = max_messages
        self.summarizer = summarizer

    def maybe_trim(self, messages: List[Dict]) -> List[Dict]:
        """
        Inspect `messages` and trim if it exceeds `max_messages`.

        The system prompt (index 0, role == "system") is always preserved.
        Tool result pairs are kept together — we never split a tool_call
        message from its corresponding tool result.

        Returns:
            A (possibly trimmed) copy of the messages list.
        """
        # Separate the system prompt from the rest
        if messages and messages[0].get("role") == "system":
            system_msg = messages[0]
            conversation = list(messages[1:])
        else:
            system_msg = None
            conversation = list(messages)

        total = len(conversation)
        if total <= self.max_messages:
            return list(messages)  # Nothing to trim

        # How many messages to evict
        evict_count = total - self.max_messages
        evicted = conversation[:evict_count]
        kept = conversation[evict_count:]

        logger.info(
            f"[ContextManager] Context trimmed: {total} → {len(kept)} messages "
            f"({evict_count} evicted)."
        )

        # Build summary injection if a summarizer is provided
        summary_msgs = []
        if self.summarizer and evicted:
            try:
                summary_text = self.summarizer(evicted)
                if summary_text:
                    summary_msgs = [{
                        "role": "user",
                        "content": (
                            f"[CONTEXT SUMMARY — earlier conversation compressed]\n{summary_text}"
                        )
                    }]
                    logger.info("[ContextManager] Summary injected for evicted messages.")
            except Exception as e:
                logger.warning(f"[ContextManager] Summarizer failed, skipping: {e}")

        # Reassemble: system → summary (optional) → kept messages
        result = []
        if system_msg:
            result.append(system_msg)
        result.extend(summary_msgs)
        result.extend(kept)
        return result
