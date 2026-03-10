import os
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from .logger import logger


class StateManager:
    """
    Provides checkpoint-based state persistence for Agent runs.

    Features:
        - Saves agent messages + metadata to a JSON checkpoint file after
          every iteration so a crashed run can be resumed exactly where
          it stopped.
        - Supports time-travel: older checkpoints are kept with sequential
          filenames so any previous state can be loaded.
        - Zero dependencies — uses only stdlib ``json`` and ``os``.

    Usage (saving / resuming)::

        # First run — will auto-save checkpoints
        agent = Agent(
            name="DevAgent",
            system_prompt="...",
            checkpoint_dir="./runs/my_task"
        )

        # Resumed run — load from latest checkpoint
        agent = Agent(
            name="DevAgent",
            system_prompt="...",
            checkpoint_dir="./runs/my_task",
            resume_from_checkpoint="./runs/my_task/checkpoint_latest.json"
        )
    """

    LATEST_FILENAME = "checkpoint_latest.json"

    def __init__(self, checkpoint_dir: str, agent_name: str):
        """
        Args:
            checkpoint_dir: Directory where checkpoint files are written.
                            Created automatically if it doesn't exist.
            agent_name:     Identifier included in checkpoint metadata.
        """
        self.checkpoint_dir = checkpoint_dir
        self.agent_name = agent_name
        self.run_id: str = str(uuid.uuid4())
        self._iteration_count: int = 0
        os.makedirs(checkpoint_dir, exist_ok=True)
        logger.info(
            f"[StateManager] Initialized for agent '{agent_name}'. "
            f"run_id={self.run_id}, dir={checkpoint_dir}"
        )

    # ------------------------------------------------------------------
    # Saving
    # ------------------------------------------------------------------

    def save(self, messages: List[Dict], extra: Optional[Dict] = None) -> str:
        """
        Persist the current message list to disk.

        Two files are written on every save:
        1. A timestamped versioned file  (e.g. ``checkpoint_003.json``)
        2. ``checkpoint_latest.json`` — always points to the most recent state.

        Args:
            messages:  The agent's current ``self.messages`` list.
            extra:     Optional dict of additional metadata to store
                       (e.g. current task description, loop index).

        Returns:
            Absolute path to the versioned checkpoint file.
        """
        self._iteration_count += 1
        timestamp = datetime.now(timezone.utc).isoformat()

        payload = {
            "run_id": self.run_id,
            "agent_name": self.agent_name,
            "iteration": self._iteration_count,
            "saved_at": timestamp,
            "messages": messages,
            "extra": extra or {},
        }

        # Write versioned checkpoint
        versioned_name = f"checkpoint_{self._iteration_count:04d}.json"
        versioned_path = os.path.join(self.checkpoint_dir, versioned_name)
        self._write_json(versioned_path, payload)

        # Overwrite the "latest" pointer
        latest_path = os.path.join(self.checkpoint_dir, self.LATEST_FILENAME)
        self._write_json(latest_path, payload)

        logger.info(f"[StateManager] Checkpoint saved → {versioned_path}")
        return versioned_path

    # ------------------------------------------------------------------
    # Loading / Resuming
    # ------------------------------------------------------------------

    @staticmethod
    def load(checkpoint_path: str) -> Dict[str, Any]:
        """
        Load a checkpoint from disk.

        Args:
            checkpoint_path: Path to the JSON checkpoint file.

        Returns:
            The deserialized checkpoint dict, containing at minimum:
            ``run_id``, ``agent_name``, ``iteration``, ``saved_at``,
            ``messages``, and ``extra``.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError:        If the file is not valid JSON or missing
                               the ``messages`` key.
        """
        if not os.path.exists(checkpoint_path):
            raise FileNotFoundError(
                f"[StateManager] Checkpoint not found: {checkpoint_path}"
            )

        with open(checkpoint_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"[StateManager] Checkpoint file is invalid JSON: {e}"
                )

        if "messages" not in data:
            raise ValueError(
                "[StateManager] Checkpoint file is missing 'messages' key."
            )

        logger.info(
            f"[StateManager] Loaded checkpoint: agent='{data.get('agent_name')}', "
            f"iteration={data.get('iteration')}, saved_at={data.get('saved_at')}"
        )
        return data

    def latest_checkpoint_path(self) -> Optional[str]:
        """Return path to the latest checkpoint file, or None if none exist."""
        path = os.path.join(self.checkpoint_dir, self.LATEST_FILENAME)
        return path if os.path.exists(path) else None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _write_json(path: str, payload: Dict) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False, default=str)
