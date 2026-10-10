import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


class AuditLogger:
    def __init__(self, log_path: str = "data/audit.log"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(self, action: str, actor: str, details: Dict[str, Any]) -> None:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "action": action,
            "details": details,
        }
        with self.log_path.open("a", encoding="utf-8") as file_handle:
            file_handle.write(json.dumps(payload, sort_keys=True) + "\n")

    def read_events(self) -> List[Dict[str, Any]]:
        if not self.log_path.exists():
            return []

        events: List[Dict[str, Any]] = []
        with self.log_path.open("r", encoding="utf-8") as file_handle:
            for line in file_handle:
                if line.strip():
                    events.append(json.loads(line))
        return events
