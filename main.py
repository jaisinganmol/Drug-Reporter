import anthropic
import json
from datetime import datetime, timedelta
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic()


# --- Delivery Receipt Manager ---
class DeliveryStatus(Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    ACKNOWLEDGED = "acknowledged"
    FAILED = "failed"
    EXPIRED = "expired"


class DeliveryReceiptManager:
    def __init__(self, acknowledgment_timeout_hours: int = 24):
        self.delivery_log: dict[str, list[dict]] = {}
        self.acknowledgment_timeout = timedelta(hours=acknowledgment_timeout_hours)

    def store_receipt(self, report_id: str, pharmacy_ids: list[str],
                      status: DeliveryStatus = DeliveryStatus.DELIVERED, metadata: dict = None) -> list[dict]:
        ts = datetime.now()
        created = []
        for pid in pharmacy_ids:
            existing = self._find_receipt(report_id, pid)
            if existing:
                existing["delivery_status"] = status.value
                existing["last_updated"] = ts.isoformat()
                existing["delivery_attempts"] = existing.get("delivery_attempts", 1) + 1
                created.append(existing)
                continue
            record = {
                "pharmacy_id": pid, "report_id": report_id,
                "delivery_timestamp": ts.isoformat(), "delivery_status": status.value,
                "acknowledgment_timestamp": None, "acknowledged_by": None,
                "delivery_attempts": 1, "last_updated": ts.isoformat(),
                "expires_at": (ts + self.acknowledgment_timeout).isoformat(),
                "metadata": metadata or {}
            }
            self.delivery_log.setdefault(report_id, []).append(record)
            created.append(record)
        return created

    def mark_acknowledged(self, report_id: str, pharmacy_id: str,
                          acknowledged_by: str = None, notes: str = None) -> dict:
        record = self._find_receipt(report_id, pharmacy_id)
        if not record:
            return None
        ts = datetime.now().isoformat()
        record.update({
            "acknowledgment_timestamp": ts, "delivery_status": DeliveryStatus.ACKNOWLEDGED.value,
            "acknowledged_by": acknowledged_by, "last_updated": ts
        })
        if notes:
            record["metadata"]["acknowledgment_notes"] = notes
        return record

    def mark_failed(self, report_id: str, pharmacy_id: str, reason: str = None) -> dict:
        record = self._find_receipt(report_id, pharmacy_id)
        if not record:
            return None
        record["delivery_status"] = DeliveryStatus.FAILED.value
        record["last_updated"] = datetime.now().isoformat()
        if reason:
            record["metadata"]["failure_reason"] = reason
        return record

    def get_acknowledgment_status(self, report_id: str) -> dict:
        entries = self.delivery_log.get(report_id, [])
        ack = [e for e in entries if e["acknowledgment_timestamp"]]
        pending = [e for e in entries if not e["acknowledgment_timestamp"]
                   and e["delivery_status"] != DeliveryStatus.FAILED.value]
        failed = [e for e in entries if e["delivery_status"] == DeliveryStatus.FAILED.value]
        return {
            "report_id": report_id, "total_sent": len(entries),
            "acknowledged_count": len(ack), "pending_count": len(pending), "failed_count": len(failed),
            "acknowledgment_rate": len(ack) / len(entries) if entries else 0,
            "acknowledged": [e["pharmacy_id"] for e in ack],
            "pending": [e["pharmacy_id"] for e in pending],
            "failed": [e["pharmacy_id"] for e in failed],
            "details": entries
        }

    def get_followup_candidates(self, report_id: str) -> list[dict]:
        entries = self.delivery_log.get(report_id, [])
        now = datetime.now()
        return [
            {**e, "is_expired": now > datetime.fromisoformat(e["expires_at"])}
            for e in entries
            if not e["acknowledgment_timestamp"] and e["delivery_status"] != DeliveryStatus.FAILED.value
        ]

    def get_statistics(self) -> dict:
        total_sent = total_ack = total_pending = total_failed = 0
        for entries in self.delivery_log.values():
            total_sent += len(entries)
            total_ack += sum(1 for e in entries if e["acknowledgment_timestamp"])
            total_pending += sum(1 for e in entries if not e["acknowledgment_timestamp"]
                                 and e["delivery_status"] != DeliveryStatus.FAILED.value)
            total_failed += sum(1 for e in entries if e["delivery_status"] == DeliveryStatus.FAILED.value)
        return {
            "total_reports": len(self.delivery_log), "total_sent": total_sent,
            "total_acknowledged": total_ack, "total_pending": total_pending, "total_failed": total_failed,
            "overall_rate": total_ack / total_sent if total_sent else 0
        }

    def _find_receipt(self, report_id: str, pharmacy_id: str) -> dict:
        return next((e for e in self.delivery_log.get(report_id, []) if e["pharmacy_id"] == pharmacy_id), None)


# --- Data Management ---
class DrugReportManager:
    def __init__(self):
        self.reports = [
            {"id": "drug_report_001", "drug_name": "Amoxicillin", "batch_number": "AMX-2024-001",
             "severity": "critical", "issue": "Contamination detected - glass particles found",
             "affected_pharmacies": ["all"], "timestamp": datetime.now().isoformat(),
             "action_required": "Immediate recall - remove from shelves"},
            {"id": "drug_report_002", "drug_name": "Lisinopril", "batch_number": "LIS-2024-045",
             "severity": "warning", "issue": "Packaging defect - expiration date unclear",
             "affected_pharmacies": ["pharmacy_005", "pharmacy_012"], "timestamp": datetime.now().isoformat(),
             "action_required": "Inspect packaging, replace if needed"},
            {"id": "drug_report_003", "drug_name": "Metformin", "batch_number": "MET-2024-089",
             "severity": "info", "issue": "Supplier change notification",
             "affected_pharmacies": ["pharmacy_003"], "timestamp": datetime.now().isoformat(),
             "action_required": "Update supplier records"}
        ]
        self.pharmacies = {
            "pharmacy_001": {"name": "Downtown Pharmacy", "email": "contact@downtown-pharm.com"},
            "pharmacy_003": {"name": "Central Medical", "email": "alerts@central-med.com"},
            "pharmacy_005": {"name": "Health Plus", "email": "support@healthplus-pharm.com"},
            "pharmacy_012": {"name": "Wellness Center", "email": "ops@wellness-center.com"},
        }

    def get_drug_reports(self): return self.reports

    def get_report_details(self, report_id: str):
        return next((r for r in self.reports if r["id"] == report_id), None)

    def get_all_pharmacies(self):
        return [{"id": k, **v} for k, v in self.pharmacies.items()]

    def get_all_pharmacy_ids(self):
        return list(self.pharmacies.keys())


class PharmacyNotificationService:
    def __init__(self, receipt_manager: DeliveryReceiptManager):
        self.receipt_manager = receipt_manager

    def send_broadcast_alert(self, drug_report: dict, pharmacy_ids: list[str]) -> dict:
        self.receipt_manager.store_receipt(
            drug_report["id"], pharmacy_ids,
            metadata={"alert_type": "broadcast", "severity": drug_report["severity"]}
        )
        return {"status": "broadcast_sent", "drug": drug_report["drug_name"],
                "batch": drug_report["batch_number"], "pharmacies_notified": len(pharmacy_ids),
                "timestamp": datetime.now().isoformat()}

    def send_targeted_alert(self, pharmacy_ids: list[str], drug_report: dict) -> dict:
        self.receipt_manager.store_receipt(
            drug_report["id"], pharmacy_ids,
            metadata={"alert_type": "targeted", "severity": drug_report["severity"]}
        )
        return {"status": "targeted_sent", "drug": drug_report["drug_name"],
                "batch": drug_report["batch_number"], "pharmacies_notified": pharmacy_ids,
                "timestamp": datetime.now().isoformat()}


# --- Tools ---
broadcast_tools = [
    {"name": "get_report_details", "description": "Gets drug report details",
     "input_schema": {"type": "object", "properties": {"report_id": {"type": "string"}}, "required": ["report_id"]}},
    {"name": "broadcast_to_all_pharmacies", "description": "Broadcasts alert to ALL pharmacies",
     "input_schema": {"type": "object",
                      "properties": {"report_id": {"type": "string"}, "alert_message": {"type": "string"}},
                      "required": ["report_id", "alert_message"]}},
    {"name": "get_acknowledgment_status", "description": "Gets delivery status for a report",
     "input_schema": {"type": "object", "properties": {"report_id": {"type": "string"}}, "required": ["report_id"]}}
]

targeted_tools = [
    {"name": "get_report_details", "description": "Gets drug report details",
     "input_schema": {"type": "object", "properties": {"report_id": {"type": "string"}}, "required": ["report_id"]}},
    {"name": "get_all_pharmacies", "description": "Gets all registered pharmacies",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "alert_specific_pharmacies", "description": "Sends alert to specific pharmacies",
     "input_schema": {"type": "object", "properties": {"report_id": {"type": "string"},
                                                       "pharmacy_ids": {"type": "array", "items": {"type": "string"}},
                                                       "alert_message": {"type": "string"}},
                      "required": ["report_id", "pharmacy_ids", "alert_message"]}},
    {"name": "get_acknowledgment_status", "description": "Gets delivery status for a report",
     "input_schema": {"type": "object", "properties": {"report_id": {"type": "string"}}, "required": ["report_id"]}}
]


def process_tool(tool_name: str, tool_input: dict, drug_mgr, notif_service, receipt_mgr) -> str:
    if tool_name == "get_report_details":
        return json.dumps(drug_mgr.get_report_details(tool_input["report_id"]))
    elif tool_name == "get_all_pharmacies":
        return json.dumps({"pharmacies": drug_mgr.get_all_pharmacies()})
    elif tool_name == "broadcast_to_all_pharmacies":
        report = drug_mgr.get_report_details(tool_input["report_id"])
        if report:
            return json.dumps(notif_service.send_broadcast_alert(report, drug_mgr.get_all_pharmacy_ids()))
        return json.dumps({"error": "Report not found"})
    elif tool_name == "alert_specific_pharmacies":
        report = drug_mgr.get_report_details(tool_input["report_id"])
        if report:
            return json.dumps(notif_service.send_targeted_alert(tool_input["pharmacy_ids"], report))
        return json.dumps({"error": "Report not found"})
    elif tool_name == "get_acknowledgment_status":
        return json.dumps(receipt_mgr.get_acknowledgment_status(tool_input["report_id"]))
    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def run_agent(agent_type: str, report_id: str, drug_mgr, notif_service, receipt_mgr) -> dict:
    tools = broadcast_tools if agent_type == "broadcast" else targeted_tools
    prompt = f"Get details for report {report_id} and {'broadcast to all pharmacies' if agent_type == 'broadcast' else 'send targeted alerts to affected pharmacies'}."

    print(f"\n{'=' * 60}")
    print(f"{'BROADCAST' if agent_type == 'broadcast' else 'TARGETED'} AGENT")
    print(f"{'=' * 60}")

    messages = [{"role": "user", "content": prompt}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1024, tools=tools, messages=messages)

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, 'text'):
                    print(f"CONFIRMATION: {block.text}")
            status = receipt_mgr.get_acknowledgment_status(report_id)
            print(
                f"Delivery: {status['total_sent']} sent, {status['acknowledged_count']} ack'd, {status['pending_count']} pending")
            return {"agent": agent_type, "status": "completed", "delivery": status}

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"  -> {block.name}")
                    result = process_tool(block.name, block.input, drug_mgr, notif_service, receipt_mgr)
                    print(f"     {result[:80]}...")
                    tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
            messages.append({"role": "user", "content": tool_results})
        else:
            break
    return {"agent": agent_type, "status": "completed"}


def run_orchestrator():
    print("\n" + "=" * 60)
    print("MULTI-AGENT DRUG ALERT ORCHESTRATOR")
    print("=" * 60)

    # Shared instances
    receipt_mgr = DeliveryReceiptManager(acknowledgment_timeout_hours=24)
    drug_mgr = DrugReportManager()
    notif_service = PharmacyNotificationService(receipt_mgr)

    reports = drug_mgr.get_drug_reports()
    print(f"\nProcessing {len(reports)} reports...\n")

    for report in reports:
        print(f"--- {report['drug_name']} ({report['severity'].upper()}) ---")
        agent_type = "broadcast" if "all" in report["affected_pharmacies"] or report[
            "severity"] == "critical" else "targeted"
        run_agent(agent_type, report["id"], drug_mgr, notif_service, receipt_mgr)

    # Final summary
    print("\n" + "=" * 60)
    print("DELIVERY SUMMARY")
    print("=" * 60)
    stats = receipt_mgr.get_statistics()
    print(f"Total Reports: {stats['total_reports']}")
    print(f"Total Sent: {stats['total_sent']}")
    print(f"Acknowledged: {stats['total_acknowledged']} ({stats['overall_rate']:.0%})")
    print(f"Pending: {stats['total_pending']}")
    print(f"Failed: {stats['total_failed']}")

    # Show follow-up candidates
    print("\nFollow-up needed:")
    for report in reports:
        candidates = receipt_mgr.get_followup_candidates(report["id"])
        if candidates:
            print(f"  {report['drug_name']}: {[c['pharmacy_id'] for c in candidates]}")


if __name__ == "__main__":
    run_orchestrator()