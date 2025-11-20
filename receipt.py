from datetime import datetime, timedelta
from typing import Optional
from enum import Enum
import json


class DeliveryStatus(Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    EXPIRED = "expired"


class DeliveryReceiptManager:
    """
    Tracks delivery receipts and pharmacy acknowledgments for drug alerts.

    Features:
    - Store and track delivery receipts per report/pharmacy
    - Mark acknowledgments with timestamps
    - Get delivery statistics and summaries
    - Find pharmacies needing follow-up
    - Support for delivery expiration
    - Export/import functionality
    """

    def __init__(self, acknowledgment_timeout_hours: int = 24):
        self.delivery_log: dict[str, list[dict]] = {}
        self.acknowledgment_timeout = timedelta(hours=acknowledgment_timeout_hours)

    # --- Core Operations ---

    def store_receipt(
            self,
            report_id: str,
            pharmacy_ids: list[str],
            status: DeliveryStatus = DeliveryStatus.DELIVERED,
            metadata: Optional[dict] = None
    ) -> list[dict]:
        """
        Store delivery receipts for multiple pharmacies.
        Returns list of created receipt records.
        """
        ts = datetime.now()
        created_records = []

        for pid in pharmacy_ids:
            # Check if receipt already exists for this report/pharmacy combo
            existing = self._find_receipt(report_id, pid)
            if existing:
                # Update existing record instead of creating duplicate
                existing["delivery_status"] = status.value
                existing["last_updated"] = ts.isoformat()
                existing["delivery_attempts"] = existing.get("delivery_attempts", 1) + 1
                created_records.append(existing)
                continue

            record = {
                "pharmacy_id": pid,
                "report_id": report_id,
                "delivery_timestamp": ts.isoformat(),
                "delivery_status": status.value,
                "acknowledgment_timestamp": None,
                "acknowledged_by": None,
                "delivery_attempts": 1,
                "last_updated": ts.isoformat(),
                "expires_at": (ts + self.acknowledgment_timeout).isoformat(),
                "metadata": metadata or {}
            }
            self.delivery_log.setdefault(report_id, []).append(record)
            created_records.append(record)

        return created_records

    def mark_acknowledged(
            self,
            report_id: str,
            pharmacy_id: str,
            acknowledged_by: Optional[str] = None,
            notes: Optional[str] = None
    ) -> Optional[dict]:
        """
        Mark a pharmacy's receipt as acknowledged.
        Returns the updated record or None if not found.
        """
        record = self._find_receipt(report_id, pharmacy_id)
        if not record:
            return None

        ts = datetime.now().isoformat()
        record["acknowledgment_timestamp"] = ts
        record["delivery_status"] = DeliveryStatus.ACKNOWLEDGED.value
        record["acknowledged_by"] = acknowledged_by
        record["last_updated"] = ts

        if notes:
            record["metadata"]["acknowledgment_notes"] = notes

        return record

    def mark_failed(
            self,
            report_id: str,
            pharmacy_id: str,
            reason: Optional[str] = None
    ) -> Optional[dict]:
        """Mark a delivery as failed."""
        record = self._find_receipt(report_id, pharmacy_id)
        if not record:
            return None

        record["delivery_status"] = DeliveryStatus.FAILED.value
        record["last_updated"] = datetime.now().isoformat()
        if reason:
            record["metadata"]["failure_reason"] = reason

        return record

    # --- Query Operations ---

    def get_receipt(self, report_id: str, pharmacy_id: str) -> Optional[dict]:
        """Get a specific receipt."""
        return self._find_receipt(report_id, pharmacy_id)

    def get_all_receipts(self, report_id: str) -> list[dict]:
        """Get all receipts for a report."""
        return self.delivery_log.get(report_id, [])

    def get_acknowledgment_status(self, report_id: str) -> dict:
        """Get comprehensive status summary for a report."""
        entries = self.delivery_log.get(report_id, [])

        acknowledged = [e for e in entries if e["acknowledgment_timestamp"]]
        pending = [e for e in entries if not e["acknowledgment_timestamp"]
                   and e["delivery_status"] != DeliveryStatus.FAILED.value]
        failed = [e for e in entries if e["delivery_status"] == DeliveryStatus.FAILED.value]

        return {
            "report_id": report_id,
            "total_sent": len(entries),
            "acknowledged_count": len(acknowledged),
            "pending_count": len(pending),
            "failed_count": len(failed),
            "acknowledgment_rate": len(acknowledged) / len(entries) if entries else 0,
            "acknowledged": [e["pharmacy_id"] for e in acknowledged],
            "pending": [e["pharmacy_id"] for e in pending],
            "failed": [e["pharmacy_id"] for e in failed],
            "details": entries
        }

    def get_followup_candidates(
            self,
            report_id: str,
            include_expired: bool = True
    ) -> list[dict]:
        """
        Get pharmacies that need follow-up (not acknowledged).
        Optionally filter by expiration status.
        """
        entries = self.delivery_log.get(report_id, [])
        now = datetime.now()

        candidates = []
        for e in entries:
            if e["acknowledgment_timestamp"]:
                continue
            if e["delivery_status"] == DeliveryStatus.FAILED.value:
                continue

            # Check expiration
            expires_at = datetime.fromisoformat(e["expires_at"])
            is_expired = now > expires_at

            if is_expired and not include_expired:
                continue

            candidate = {**e, "is_expired": is_expired}
            candidates.append(candidate)

        return candidates

    def get_pharmacy_history(self, pharmacy_id: str) -> list[dict]:
        """Get all delivery receipts for a specific pharmacy across all reports."""
        history = []
        for report_id, entries in self.delivery_log.items():
            for entry in entries:
                if entry["pharmacy_id"] == pharmacy_id:
                    history.append({**entry, "report_id": report_id})

        # Sort by delivery timestamp (newest first)
        history.sort(key=lambda x: x["delivery_timestamp"], reverse=True)
        return history

    # --- Statistics ---

    def get_statistics(self) -> dict:
        """Get overall statistics across all reports."""
        total_sent = 0
        total_ack = 0
        total_pending = 0
        total_failed = 0

        report_stats = []
        for report_id, entries in self.delivery_log.items():
            ack = sum(1 for e in entries if e["acknowledgment_timestamp"])
            pending = sum(1 for e in entries if not e["acknowledgment_timestamp"]
                          and e["delivery_status"] != DeliveryStatus.FAILED.value)
            failed = sum(1 for e in entries if e["delivery_status"] == DeliveryStatus.FAILED.value)

            total_sent += len(entries)
            total_ack += ack
            total_pending += pending
            total_failed += failed

            report_stats.append({
                "report_id": report_id,
                "sent": len(entries),
                "acknowledged": ack,
                "pending": pending,
                "failed": failed,
                "rate": ack / len(entries) if entries else 0
            })

        return {
            "total_reports": len(self.delivery_log),
            "total_sent": total_sent,
            "total_acknowledged": total_ack,
            "total_pending": total_pending,
            "total_failed": total_failed,
            "overall_acknowledgment_rate": total_ack / total_sent if total_sent else 0,
            "by_report": report_stats
        }

    # --- Bulk Operations ---

    def check_expirations(self) -> list[dict]:
        """Check for expired receipts and update their status."""
        now = datetime.now()
        expired = []

        for report_id, entries in self.delivery_log.items():
            for entry in entries:
                if entry["acknowledgment_timestamp"]:
                    continue
                if entry["delivery_status"] == DeliveryStatus.EXPIRED.value:
                    continue

                expires_at = datetime.fromisoformat(entry["expires_at"])
                if now > expires_at:
                    entry["delivery_status"] = DeliveryStatus.EXPIRED.value
                    entry["last_updated"] = now.isoformat()
                    expired.append(entry)

        return expired

    def retry_failed(self, report_id: str) -> list[str]:
        """Get list of pharmacy IDs with failed deliveries for retry."""
        entries = self.delivery_log.get(report_id, [])
        return [e["pharmacy_id"] for e in entries
                if e["delivery_status"] == DeliveryStatus.FAILED.value]

    # --- Export/Import ---

    def export_to_json(self) -> str:
        """Export all delivery logs to JSON."""
        return json.dumps(self.delivery_log, indent=2)

    def import_from_json(self, json_str: str) -> None:
        """Import delivery logs from JSON."""
        self.delivery_log = json.loads(json_str)

    def reset(self, report_id: Optional[str] = None) -> None:
        """Reset delivery log. If report_id provided, only reset that report."""
        if report_id:
            self.delivery_log.pop(report_id, None)
        else:
            self.delivery_log.clear()

    # --- Private Helpers ---

    def _find_receipt(self, report_id: str, pharmacy_id: str) -> Optional[dict]:
        """Find a specific receipt by report and pharmacy ID."""
        entries = self.delivery_log.get(report_id, [])
        for entry in entries:
            if entry["pharmacy_id"] == pharmacy_id:
                return entry
        return None


# --- Example Usage ---
if __name__ == "__main__":
    # Initialize manager with 24-hour acknowledgment timeout
    manager = DeliveryReceiptManager(acknowledgment_timeout_hours=24)

    # Store receipts for a broadcast alert
    manager.store_receipt(
        report_id="drug_report_001",
        pharmacy_ids=["pharmacy_001", "pharmacy_003", "pharmacy_005", "pharmacy_012"],
        metadata={"alert_type": "broadcast", "severity": "critical"}
    )

    # Store receipts for a targeted alert
    manager.store_receipt(
        report_id="drug_report_002",
        pharmacy_ids=["pharmacy_005", "pharmacy_012"],
        metadata={"alert_type": "targeted", "severity": "warning"}
    )

    # Simulate acknowledgments
    manager.mark_acknowledged("drug_report_001", "pharmacy_001", acknowledged_by="John Doe")
    manager.mark_acknowledged("drug_report_001", "pharmacy_003")

    # Mark a failed delivery
    manager.mark_failed("drug_report_001", "pharmacy_012", reason="Invalid email address")

    # Get status for a report
    status = manager.get_acknowledgment_status("drug_report_001")
    print("Report Status:")
    print(f"  Sent: {status['total_sent']}")
    print(f"  Acknowledged: {status['acknowledged_count']} ({status['acknowledgment_rate']:.0%})")
    print(f"  Pending: {status['pending']}")
    print(f"  Failed: {status['failed']}")

    # Get follow-up candidates
    followups = manager.get_followup_candidates("drug_report_001")
    print(f"\nNeed follow-up: {[f['pharmacy_id'] for f in followups]}")

    # Get overall statistics
    stats = manager.get_statistics()
    print(f"\nOverall Stats:")
    print(f"  Total reports: {stats['total_reports']}")
    print(f"  Overall ack rate: {stats['overall_acknowledgment_rate']:.0%}")