"""
Status file management for batch simulations.

Provides utilities to read, write, and update status files that track
the progress of batch simulation runs.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List


class BatchStatus:
    """
    Manages status tracking for batch simulation runs.

    Status files are stored in results/.batch/{batch_id}/status.json
    """

    # Status constants
    STATUS_PENDING = "pending"
    STATUS_RUNNING = "running"
    STATUS_COMPLETED = "completed"
    STATUS_ERROR = "error"
    STATUS_CANCELLED = "cancelled"

    def __init__(self, batch_dir: Path):
        """
        Initialize batch status manager.

        Args:
            batch_dir: Directory for this batch (e.g., results/.batch/{batch_id})
        """
        self.batch_dir = Path(batch_dir)
        self.status_file = self.batch_dir / "status.json"
        self.summary_file = self.batch_dir / "summary.json"

    def initialize(
        self,
        batch_id: str,
        protocols: List[str],
        n_patients: int,
        duration_years: float,
        seed: int,
        pid: Optional[int] = None
    ):
        """
        Initialize a new batch status file.

        Args:
            batch_id: Unique batch identifier
            protocols: List of protocol names
            n_patients: Number of patients per simulation
            duration_years: Duration in years per simulation
            seed: Random seed
            pid: Process ID of the subprocess
        """
        # Ensure directory exists
        self.batch_dir.mkdir(parents=True, exist_ok=True)

        status = {
            "status": self.STATUS_PENDING,
            "batch_id": batch_id,
            "pid": pid,
            "started_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "parameters": {
                "n_patients": n_patients,
                "duration_years": duration_years,
                "seed": seed
            },
            "protocols": protocols,
            "current_protocol": None,
            "current_protocol_index": 0,
            "progress": "Initializing...",
            "completed_simulations": [],
            "remaining_protocols": protocols.copy(),
            "error": None
        }

        self._write_status(status)

    def update(
        self,
        status: Optional[str] = None,
        current_protocol: Optional[str] = None,
        current_protocol_index: Optional[int] = None,
        progress: Optional[str] = None,
        error: Optional[str] = None
    ):
        """
        Update the status file with new information.

        Args:
            status: New status value
            current_protocol: Name of protocol currently being processed
            current_protocol_index: Index of current protocol
            progress: Progress message
            error: Error message if any
        """
        current = self.read()
        if not current:
            raise ValueError("Status file not initialized")

        if status is not None:
            current["status"] = status
        if current_protocol is not None:
            current["current_protocol"] = current_protocol
        if current_protocol_index is not None:
            current["current_protocol_index"] = current_protocol_index
        if progress is not None:
            current["progress"] = progress
        if error is not None:
            current["error"] = error

        current["updated_at"] = datetime.now().isoformat()

        self._write_status(current)

    def add_completed_simulation(
        self,
        protocol: str,
        sim_id: str,
        n_patients: int,
        runtime: float
    ):
        """
        Mark a simulation as completed.

        Args:
            protocol: Protocol name
            sim_id: Simulation ID
            n_patients: Number of patients
            runtime: Runtime in seconds
        """
        current = self.read()
        if not current:
            raise ValueError("Status file not initialized")

        # Add to completed list
        current["completed_simulations"].append({
            "protocol": protocol,
            "sim_id": sim_id,
            "n_patients": n_patients,
            "runtime": runtime,
            "completed_at": datetime.now().isoformat()
        })

        # Remove from remaining list
        if protocol in current["remaining_protocols"]:
            current["remaining_protocols"].remove(protocol)

        current["updated_at"] = datetime.now().isoformat()

        self._write_status(current)

    def mark_completed(self):
        """Mark the batch as fully completed."""
        current = self.read()
        if not current:
            raise ValueError("Status file not initialized")

        current["status"] = self.STATUS_COMPLETED
        current["progress"] = "All simulations completed"
        current["completed_at"] = datetime.now().isoformat()
        current["updated_at"] = datetime.now().isoformat()

        self._write_status(current)

    def mark_error(self, error_message: str):
        """
        Mark the batch as failed with an error.

        Args:
            error_message: Error description
        """
        current = self.read()
        if not current:
            raise ValueError("Status file not initialized")

        current["status"] = self.STATUS_ERROR
        current["error"] = error_message
        current["updated_at"] = datetime.now().isoformat()

        self._write_status(current)

    def mark_cancelled(self):
        """Mark the batch as cancelled."""
        current = self.read()
        if not current:
            raise ValueError("Status file not initialized")

        current["status"] = self.STATUS_CANCELLED
        current["progress"] = "Batch cancelled by user"
        current["updated_at"] = datetime.now().isoformat()

        self._write_status(current)

    def read(self) -> Optional[Dict[str, Any]]:
        """
        Read the current status.

        Returns:
            Status dictionary or None if file doesn't exist
        """
        if not self.status_file.exists():
            return None

        try:
            with open(self.status_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def is_running(self) -> bool:
        """Check if the batch is currently running."""
        status = self.read()
        return status and status["status"] in [self.STATUS_PENDING, self.STATUS_RUNNING]

    def is_completed(self) -> bool:
        """Check if the batch has completed."""
        status = self.read()
        return status and status["status"] == self.STATUS_COMPLETED

    def has_error(self) -> bool:
        """Check if the batch has an error."""
        status = self.read()
        return status and status["status"] == self.STATUS_ERROR

    def get_pid(self) -> Optional[int]:
        """Get the process ID of the batch runner."""
        status = self.read()
        return status["pid"] if status else None

    def write_summary(self, summary: Dict[str, Any]):
        """
        Write final summary statistics.

        Args:
            summary: Summary dictionary with statistics
        """
        with open(self.summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

    def read_summary(self) -> Optional[Dict[str, Any]]:
        """
        Read the summary statistics.

        Returns:
            Summary dictionary or None if file doesn't exist
        """
        if not self.summary_file.exists():
            return None

        try:
            with open(self.summary_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _write_status(self, status: Dict[str, Any]):
        """Internal method to write status to file."""
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2)


def get_batch_dir(batch_id: str) -> Path:
    """
    Get the batch directory for a given batch ID.

    Args:
        batch_id: Batch identifier

    Returns:
        Path to batch directory
    """
    from ape.core.results.factory import ResultsFactory
    return ResultsFactory.DEFAULT_RESULTS_DIR / ".batch" / batch_id


def list_batches() -> List[Dict[str, Any]]:
    """
    List all batch runs with their status.

    Returns:
        List of batch info dictionaries
    """
    from ape.core.results.factory import ResultsFactory
    batch_base = ResultsFactory.DEFAULT_RESULTS_DIR / ".batch"

    if not batch_base.exists():
        return []

    batches = []
    for batch_dir in batch_base.iterdir():
        if batch_dir.is_dir():
            status_mgr = BatchStatus(batch_dir)
            status = status_mgr.read()
            if status:
                batches.append({
                    "batch_id": batch_dir.name,
                    "status": status["status"],
                    "started_at": status.get("started_at"),
                    "protocols": status.get("protocols", []),
                    "completed_count": len(status.get("completed_simulations", [])),
                    "total_count": len(status.get("protocols", []))
                })

    # Sort by start time, most recent first
    batches.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    return batches


def cleanup_old_batches(keep_n: int = 10):
    """
    Clean up old batch directories, keeping only the N most recent.

    Args:
        keep_n: Number of batches to keep
    """
    batches = list_batches()
    if len(batches) <= keep_n:
        return

    # Delete oldest batches
    for batch in batches[keep_n:]:
        batch_dir = get_batch_dir(batch["batch_id"])
        if batch_dir.exists():
            import shutil
            shutil.rmtree(batch_dir)
