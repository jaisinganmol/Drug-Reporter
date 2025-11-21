# langchain_tools.py
# Tool wrappers for Drug-Reporter agent orchestration

import os
from dotenv import load_dotenv
from langchain.tools import tool
from agents import AgentFactory
from utils import (
    generate_id,
    calculate_acknowledgment_rate,
    format_delivery_report,
)

load_dotenv()
API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Initialize agents
agent_factory = AgentFactory()
broadcast_agent = agent_factory.create_agent('broadcast', API_KEY)
targeted_agent = agent_factory.create_agent('targeted', API_KEY)

pharmacies = []
drug_reports = {}

@tool
def load_sample_pharmacies() -> str:
    """Load sample pharmacies into the system."""
    global pharmacies
    pharmacies = [
        {'id': generate_id('PHARM'), 'name': 'Downtown Pharmacy', 'location': 'New York', 'region': 'Northeast', 'pharmacy_type': 'Independent'},
        {'id': generate_id('PHARM'), 'name': 'Main Street Pharmacy', 'location': 'New York', 'region': 'Northeast', 'pharmacy_type': 'Chain'},
        {'id': generate_id('PHARM'), 'name': 'West Side Pharmacy', 'location': 'Los Angeles', 'region': 'West', 'pharmacy_type': 'Independent'},
        {'id': generate_id('PHARM'), 'name': 'Central Pharmacy', 'location': 'Chicago', 'region': 'Midwest', 'pharmacy_type': 'Chain'},
    ]
    return f"Loaded {len(pharmacies)} pharmacies"

@tool
def create_drug_report(
    drug_name: str,
    alert_type: str,
    severity: str,
    description: str,
    action_required: str,
) -> str:
    """
    Create a new drug safety report.
    """
    import datetime
    report_id = generate_id('DRUG')
    drug_reports[report_id] = {
        'id': report_id,
        'drug_name': drug_name,
        'alert_type': alert_type,
        'severity': severity,
        'description': description,
        'action_required': action_required,
        'created_at': datetime.datetime.now().isoformat(),
        'regions_affected': ['Northeast', 'Midwest', 'West'],
    }
    return f"Created report {report_id} for {drug_name}"

@tool
def broadcast_alert(report_id: str) -> str:
    """
    Broadcast alert to ALL pharmacies for major recalls.
    """
    if report_id not in drug_reports:
        return f"Error: Report {report_id} not found"
    if not pharmacies:
        return "Error: No pharmacies loaded. Call load_sample_pharmacies first."
    results = broadcast_agent.send_alert(drug_reports[report_id], pharmacies)
    return format_delivery_report(results)

@tool
def targeted_alert(report_id: str, regions: str) -> str:
    """
    Send alert to specified regions only.
    """
    if report_id not in drug_reports:
        return f"Error: Report {report_id} not found"
    if not pharmacies:
        return "Error: No pharmacies loaded. Call load_sample_pharmacies first."
    region_list = [r.strip() for r in regions.split(',')]
    criteria = {'regions_affected': region_list}
    results = targeted_agent.send_alert(drug_reports[report_id], pharmacies, criteria)
    return format_delivery_report(results)

@tool
def check_delivery_statistics() -> str:
    """Return delivery and acknowledgment statistics for all alerts."""
    all_receipts = broadcast_agent.delivery_receipts + targeted_agent.delivery_receipts
    if not all_receipts:
        return "No delivery receipts yet."
    stats = calculate_acknowledgment_rate(all_receipts)
    return (
        f"Delivery Statistics:\n"
        f"- Total: {stats['total_receipts']}\n"
        f"- Acknowledged: {stats['acknowledged']} ({stats['acknowledgment_rate']:.1f}%)\n"
        f"- Pending: {stats['pending']} ({stats['pending_rate']:.1f}%)\n"
        f"- Failed: {stats['failed']} ({stats['failure_rate']:.1f}%)"
    )

@tool
def send_followup_reminders() -> str:
    """Send reminders to pharmacies that haven't acknowledged."""
    pending = broadcast_agent.get_pending_receipts()
    if not pending:
        return "No pending receipts to follow up on."
    results = broadcast_agent.send_follow_up([r['id'] for r in pending])
    return f"Follow-ups sent: {results['follow_ups_sent']}, Already ack'd: {results['already_acknowledged']}"

all_tools = [
    load_sample_pharmacies,
    create_drug_report,
    broadcast_alert,
    targeted_alert,
    check_delivery_statistics,
    send_followup_reminders,
]
