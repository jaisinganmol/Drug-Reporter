import streamlit as st
import anthropic
import json
from datetime import datetime, timedelta
from enum import Enum
import time
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
                "pharmacy_id": pid, "report": report_id,
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
                "pharmacies_notified": len(pharmacy_ids), "timestamp": datetime.now().isoformat()}

    def send_targeted_alert(self, pharmacy_ids: list[str], drug_report: dict) -> dict:
        self.receipt_manager.store_receipt(
            drug_report["id"], pharmacy_ids,
            metadata={"alert_type": "targeted", "severity": drug_report["severity"]}
        )
        return {"status": "targeted_sent", "drug": drug_report["drug_name"],
                "pharmacies_notified": pharmacy_ids, "timestamp": datetime.now().isoformat()}


# --- Tools ---
broadcast_tools = [
    {"name": "get_report_details", "description": "Gets drug report details",
     "input_schema": {"type": "object", "properties": {"report_id": {"type": "string"}}, "required": ["report_id"]}},
    {"name": "broadcast_to_all_pharmacies", "description": "Broadcasts alert to ALL pharmacies",
     "input_schema": {"type": "object",
                      "properties": {"report_id": {"type": "string"}, "alert_message": {"type": "string"}},
                      "required": ["report_id", "alert_message"]}}
]

targeted_tools = [
    {"name": "get_report_details", "description": "Gets drug report details",
     "input_schema": {"type": "object", "properties": {"report_id": {"type": "string"}}, "required": ["report_id"]}},
    {"name": "alert_specific_pharmacies", "description": "Sends alert to specific pharmacies",
     "input_schema": {"type": "object", "properties": {"report_id": {"type": "string"},
                                                       "pharmacy_ids": {"type": "array", "items": {"type": "string"}},
                                                       "alert_message": {"type": "string"}},
                      "required": ["report_id", "pharmacy_ids", "alert_message"]}}
]

def process_tool(tool_name, tool_input, drug_mgr, notif_service, all_reports, all_pharmacy_ids):
    report = drug_mgr.get_report_details(tool_input.get("report_id", ""))
    if not report:
        report = next((r for r in all_reports if r["id"] == tool_input.get("report_id")), None)
    if tool_name == "get_report_details":
        return json.dumps(report) if report else json.dumps({"error": "Not found"})
    elif tool_name == "broadcast_to_all_pharmacies":
        if report:
            return json.dumps(notif_service.send_broadcast_alert(report, all_pharmacy_ids))
        return json.dumps({"error": "Report not found"})
    elif tool_name == "alert_specific_pharmacies":
        if report:
            return json.dumps(notif_service.send_targeted_alert(tool_input["pharmacy_ids"], report))
        return json.dumps({"error": "Report not found"})
    return json.dumps({"error": f"Unknown tool: {tool_name}"})

def run_agent(report_id, alert_type, pharmacy_ids, all_reports, receipt_mgr, all_pharmacy_ids):
    drug_mgr = DrugReportManager()
    notif_service = PharmacyNotificationService(receipt_mgr)

    tools = broadcast_tools if alert_type == "broadcast" else targeted_tools
    if alert_type == "broadcast":
        prompt = f"Get details for report {report_id} and broadcast to all pharmacies."
    else:
        prompt = f"Get details for report {report_id} and alert these pharmacies: {', '.join(pharmacy_ids)}"

    messages = [{"role": "user", "content": prompt}]
    execution_log = []

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-20250514", max_tokens=1024, tools=tools, messages=messages)

        if response.stop_reason == "end_turn":
            for block in response.content:
                if hasattr(block, 'text'):
                    return block.text, execution_log, receipt_mgr.get_acknowledgment_status(report_id)

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    execution_log.append(f"Tool: {block.name}")
                    result = process_tool(block.name, block.input, drug_mgr, notif_service,
                                          all_reports, all_pharmacy_ids)
                    execution_log.append(f"Result: {result[:150]}")
                    tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": result})
            messages.append({"role": "user", "content": tool_results})
        else:
            break
    return "Agent completed", execution_log, receipt_mgr.get_acknowledgment_status(report_id)

def main():
    st.set_page_config(page_title="Pharmacy Alert System", layout="wide")
    st.title("Drug Alert System - Control Center")
    if 'receipt_mgr' not in st.session_state:
        st.session_state.receipt_mgr = DeliveryReceiptManager(acknowledgment_timeout_hours=24)
    if 'alert_sent' not in st.session_state:
        st.session_state.alert_sent = False
    if 'custom_reports' not in st.session_state:
        st.session_state.custom_reports = []
    if 'custom_pharmacies' not in st.session_state:
        st.session_state.custom_pharmacies = []
    drug_mgr = DrugReportManager()
    reports = drug_mgr.get_drug_reports() + st.session_state.custom_reports
    all_pharmacies = drug_mgr.get_all_pharmacies() + st.session_state.custom_pharmacies
    seen_ids = set()
    pharmacies = []
    for p in all_pharmacies:
        if p["id"] not in seen_ids:
            seen_ids.add(p["id"])
            pharmacies.append(p)
    all_pharmacy_ids = [p["id"] for p in pharmacies]
    with st.sidebar:
        st.header("Drug Reports")
        tab1, tab2, tab3, tab4 = st.tabs(["View", "Create", "Pharmacy", "Stats"])
        with tab1:
            selected_report_id = st.selectbox(
                "Choose Report", options=[r["id"] for r in reports],
                format_func=lambda x: f"{next(r['drug_name'] for r in reports if r['id'] == x)}")
        with tab2:
            with st.form("new_report"):
                drug_name = st.text_input("Drug Name")
                batch_number = st.text_input("Batch Number")
                severity = st.selectbox("Severity", ["critical", "warning", "info"])
                issue = st.text_area("Issue", height=80)
                action_required = st.text_area("Action Required", height=60)
                affect_all = st.checkbox("All Pharmacies")
                affected = [] if affect_all else st.multiselect(
                    "Select Pharmacies", [p["id"] for p in pharmacies],
                    format_func=lambda x: next((p['name'] for p in pharmacies if p['id'] == x), x))
                if st.form_submit_button("Create"):
                    if drug_name and batch_number and issue:
                        new_id = f"drug_report_{int(time.time())}"
                        st.session_state.custom_reports.append({
                            "id": new_id, "drug_name": drug_name, "batch_number": batch_number,
                            "severity": severity, "issue": issue, "action_required": action_required,
                            "affected_pharmacies": ["all"] if affect_all else affected,
                            "timestamp": datetime.now().isoformat()
                        })
                        st.success(f"Created: {drug_name}")
                        st.rerun()
                    else:
                        st.error("Fill required fields")
        with tab3:
            with st.form("new_pharmacy"):
                name = st.text_input("Pharmacy Name")
                email = st.text_input("Email")
                if st.form_submit_button("Add"):
                    if name and email:
                        new_id = f"pharmacy_{int(time.time())}"
                        st.session_state.custom_pharmacies.append({"id": new_id, "name": name, "email": email})
                        st.success(f"Added: {name}")
                        st.rerun()
                    else:
                        st.error("Fill required fields")
        with tab4:
            stats = st.session_state.receipt_mgr.get_statistics()
            st.metric("Total Reports", stats["total_reports"])
            st.metric("Total Sent", stats["total_sent"])
            st.metric("Acknowledged", f"{stats['total_acknowledged']} ({stats['overall_rate']:.0%})")
            st.metric("Pending", stats["total_pending"])
            st.metric("Failed", stats["total_failed"])
    selected_report = next((r for r in reports if r["id"] == selected_report_id), None)
    if not selected_report:
        st.error("Report not found")
        return
    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.subheader("Report Details")
        st.markdown(f"{selected_report['severity'].upper()}: {selected_report['drug_name']}")
        st.markdown(f"Batch: `{selected_report['batch_number']}`")
        st.markdown(f"**Issue:** {selected_report['issue']}")
        st.markdown(f"**Action:** {selected_report['action_required']}")
        if selected_report['affected_pharmacies'] == ["all"]:
            st.info("Recommended: Broadcast to ALL")
        else:
            st.info(f"Recommended: {', '.join(selected_report['affected_pharmacies'])}")
    with col2:
        st.subheader("Alert Configuration")
        alert_type = st.radio("Alert Type", ["broadcast", "targeted"],
                              format_func=lambda x: "Broadcast ALL" if x == "broadcast" else "Targeted",
                              horizontal=True)
        selected_pharmacies = []
        if alert_type == "targeted":
            for p in pharmacies:
                recommended = p["id"] in selected_report.get('affected_pharmacies', [])
                label = f"{p['name']}" + (" (Recommended)" if recommended else "")
                if st.checkbox(label, value=recommended, key=f"select_{p['id']}"):
                    selected_pharmacies.append(p["id"])
            if not selected_pharmacies:
                st.warning("Select at least one pharmacy")
        else:
            selected_pharmacies = all_pharmacy_ids
        can_send = alert_type == "broadcast" or selected_pharmacies
        if st.button("Send Alert", type="primary", disabled=not can_send, use_container_width=True):
            with st.spinner("Sending..."):
                confirmation, log, delivery_status = run_agent(
                    selected_report_id, alert_type, selected_pharmacies,
                    reports, st.session_state.receipt_mgr, all_pharmacy_ids)
                st.session_state.alert_sent = True
                st.session_state.confirmation = confirmation
                st.session_state.execution_log = log
                st.session_state.delivery_status = delivery_status
                st.session_state.last_report_id = selected_report_id
    if st.session_state.alert_sent:
        st.divider()
        st.subheader("Alert Results")
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.success("Alert sent!")
            st.markdown(st.session_state.confirmation)
            with st.expander("Execution Log"):
                for entry in st.session_state.execution_log:
                    st.code(entry)
        with col2:
            status = st.session_state.delivery_status
            st.metric("Sent", status['total_sent'])
            st.metric("Acknowledged", status['acknowledged_count'])
            st.metric("Pending", status['pending_count'])
            if status['failed_count']:
                st.metric("Failed", status['failed_count'])
        with col3:
            st.markdown("**Pending Acknowledgments:**")
            report_id = st.session_state.last_report_id
            for pid in status.get('pending', []):
                pharmacy_name = next((p['name'] for p in pharmacies if p['id'] == pid), pid)
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.text(pharmacy_name)
                with col_b:
                    if st.button("Acknowledge", key=f"ack_{pid}", help=f"Acknowledge {pharmacy_name}"):
                        st.session_state.receipt_mgr.mark_acknowledged(report_id, pid)
                        st.session_state.delivery_status = st.session_state.receipt_mgr.get_acknowledgment_status(report_id)
                        st.rerun()
            st.divider()
            if st.button("Send Another Alert", use_container_width=True):
                st.session_state.alert_sent = False
                st.rerun()

if __name__ == "__main__":
    main()
