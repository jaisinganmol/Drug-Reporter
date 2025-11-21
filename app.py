# app.py
import streamlit as st
import os
import json
from dotenv import load_dotenv
from datetime import datetime
from agents import AgentFactory
from models import DrugReport, Pharmacy
from utils import (
    generate_id,
    validate_email,
    validate_phone,
    create_alert_summary,
    calculate_acknowledgment_rate,
    get_severity_color
)

# Load environment variables
load_dotenv()
API_KEY = os.getenv('ANTHROPIC_API_KEY')

if not API_KEY:
    st.error("ANTHROPIC_API_KEY not found in .env file")
    st.stop()

# Page config
st.set_page_config(
    page_title="Drug Reporter",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# Function to load default data
def load_default_data():
    """Load default pharmacies and drug reports"""
    default_pharmacies = [
        {
            'id': 'PHARM-NYC001',
            'name': 'Downtown Pharmacy NYC',
            'location': 'New York',
            'phone': '555-0001',
            'email': 'downtown@pharmacy.com',
            'pharmacy_type': 'Independent',
            'region': 'Northeast',
            'created_at': datetime.now().isoformat()
        },
        {
            'id': 'PHARM-NYC002',
            'name': 'Main Street Pharmacy',
            'location': 'New York',
            'phone': '555-0002',
            'email': 'mainst@pharmacy.com',
            'pharmacy_type': 'Chain',
            'region': 'Northeast',
            'created_at': datetime.now().isoformat()
        },
        {
            'id': 'PHARM-LA001',
            'name': 'West Side Pharmacy',
            'location': 'Los Angeles',
            'phone': '555-0003',
            'email': 'westside@pharmacy.com',
            'pharmacy_type': 'Independent',
            'region': 'West',
            'created_at': datetime.now().isoformat()
        },
        {
            'id': 'PHARM-CHI001',
            'name': 'Central Pharmacy',
            'location': 'Chicago',
            'phone': '555-0004',
            'email': 'central@pharmacy.com',
            'pharmacy_type': 'Chain',
            'region': 'Midwest',
            'created_at': datetime.now().isoformat()
        },
        {
            'id': 'PHARM-MIA001',
            'name': 'Sunrise Hospital Pharmacy',
            'location': 'Miami',
            'phone': '555-0005',
            'email': 'sunrise@pharmacy.com',
            'pharmacy_type': 'Hospital',
            'region': 'Southeast',
            'created_at': datetime.now().isoformat()
        }
    ]

    default_drug_reports = [
        {
            'id': 'DRUG-001',
            'drug_name': 'Metformin XR 500mg',
            'alert_type': 'Safety Warning',
            'severity': 'High',
            'description': 'Potential contamination detected in batch numbers 12345-12500. Affected batches may contain glass particles.',
            'action_required': 'Immediately notify all patients. Recall all affected batches. Check inventory against batch numbers.',
            'created_at': datetime.now().isoformat(),
            'created_by': 'FDA Safety Team',
            'manufacturer': 'Pharma Corp Inc.',
            'affected_batches': ['12345-12500'],
            'regions_affected': ['Northeast', 'Midwest']
        },
        {
            'id': 'DRUG-002',
            'drug_name': 'Lisinopril 10mg',
            'alert_type': 'Recall',
            'severity': 'Critical',
            'description': 'Manufacturing defect found in tablets. Some tablets may not contain the correct amount of active ingredient.',
            'action_required': 'Stop dispensing immediately. Contact all patients who received this medication. Report to poison control.',
            'created_at': datetime.now().isoformat(),
            'created_by': 'FDA Safety Team',
            'manufacturer': 'Generic Meds Ltd',
            'affected_batches': ['LIS-2024-001', 'LIS-2024-002'],
            'regions_affected': ['West', 'Southwest']
        },
        {
            'id': 'DRUG-003',
            'drug_name': 'Atorvastatin 20mg',
            'alert_type': 'Contraindication',
            'severity': 'Medium',
            'description': 'New drug interaction discovered with common over-the-counter pain relievers.',
            'action_required': 'Review patient medication lists. Counsel patients to avoid NSAIDs. Consider alternative statins if needed.',
            'created_at': datetime.now().isoformat(),
            'created_by': 'FDA Safety Team',
            'manufacturer': 'Cardio Pharma',
            'affected_batches': [],
            'regions_affected': ['All']
        }
    ]

    return default_pharmacies, default_drug_reports


# Initialize session state
if 'pharmacies' not in st.session_state:
    default_pharmacies, default_drug_reports = load_default_data()
    st.session_state.pharmacies = default_pharmacies
    st.session_state.drug_reports = default_drug_reports
else:
    # Ensure drug_reports exists
    if 'drug_reports' not in st.session_state:
        _, default_drug_reports = load_default_data()
        st.session_state.drug_reports = default_drug_reports

if 'broadcast_agent' not in st.session_state:
    st.session_state.broadcast_agent = AgentFactory.create_agent('broadcast', API_KEY)

if 'targeted_agent' not in st.session_state:
    st.session_state.targeted_agent = AgentFactory.create_agent('targeted', API_KEY)

if 'delivery_receipts' not in st.session_state:
    st.session_state.delivery_receipts = []

# Main app
st.title("Drug Reporter System")
st.markdown("Multi-Agent Drug Safety Alert Management")

# Sidebar navigation
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Select a page:",
        [
            "Dashboard",
            "Create Drug Report",
            "Manage Pharmacies",
            "Send Alerts",
            "Track Deliveries",
            "Statistics"
        ]
    )

    st.divider()
    st.subheader("Quick Stats")
    st.metric("Pharmacies", len(st.session_state.pharmacies))
    st.metric("Drug Reports", len(st.session_state.drug_reports))
    st.metric("Total Deliveries", len(st.session_state.delivery_receipts))

# Dashboard Page
if page == "Dashboard":
    st.header("Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Pharmacies", len(st.session_state.pharmacies))

    with col2:
        st.metric("Drug Reports", len(st.session_state.drug_reports))

    with col3:
        total_receipts = len(st.session_state.delivery_receipts)
        st.metric("Total Deliveries", total_receipts)

    with col4:
        acknowledged = len([r for r in st.session_state.delivery_receipts
                            if r.get('status') == 'acknowledged'])
        st.metric("Acknowledged", acknowledged)

    st.divider()

    # System Info
    st.subheader("System Information")
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Default Pharmacies Loaded:**")
        for pharm in st.session_state.pharmacies[:3]:
            st.write(f"• {pharm['name']} ({pharm['pharmacy_type']})")

    with col2:
        st.write("**Default Drug Reports Loaded:**")
        for report in st.session_state.drug_reports[:3]:
            st.write(f"• {report['drug_name']} ({report['severity']})")

    st.divider()

    # Recent deliveries
    st.subheader("Recent Deliveries")
    if st.session_state.delivery_receipts:
        receipts_df = st.session_state.delivery_receipts[-10:]
        st.dataframe(receipts_df, use_container_width=True)
    else:
        st.info("No deliveries yet. Try sending an alert!")

# Create Drug Report Page
elif page == "Create Drug Report":
    st.header("Create Drug Report")

    with st.form("drug_report_form"):
        col1, col2 = st.columns(2)

        with col1:
            drug_name = st.text_input("Drug Name", placeholder="e.g., Metformin XR 500mg")
            alert_type = st.selectbox("Alert Type", ["Recall", "Safety Warning", "Contraindication", "Other"])
            severity = st.selectbox("Severity", ["Critical", "High", "Medium", "Low"])

        with col2:
            manufacturer = st.text_input("Manufacturer", placeholder="e.g., Pharma Corp")
            affected_batches = st.text_area("Affected Batches (one per line)")

        description = st.text_area("Description", height=150)
        action_required = st.text_area("Action Required", height=100)

        submitted = st.form_submit_button("Create Report", use_container_width=True)

        if submitted:
            if not drug_name or not description or not action_required:
                st.error("Please fill in all required fields")
            else:
                report = {
                    'id': generate_id('DRUG'),
                    'drug_name': drug_name,
                    'alert_type': alert_type,
                    'severity': severity,
                    'description': description,
                    'action_required': action_required,
                    'created_at': datetime.now().isoformat(),
                    'created_by': 'System User',
                    'manufacturer': manufacturer,
                    'affected_batches': affected_batches.split('\n') if affected_batches else []
                }

                st.session_state.drug_reports.append(report)
                st.success(f"Drug report created: {report['id']}")
                st.json(report)

# Manage Pharmacies Page
elif page == "Manage Pharmacies":
    st.header("Manage Pharmacies")

    tab1, tab2 = st.tabs(["Add Pharmacy", "View Pharmacies"])

    with tab1:
        with st.form("pharmacy_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("Pharmacy Name")
                email = st.text_input("Email")
                phone = st.text_input("Phone")

            with col2:
                location = st.text_input("Location")
                pharmacy_type = st.selectbox("Type", ["Independent", "Chain", "Hospital"])
                region = st.text_input("Region")

            submitted = st.form_submit_button("Add Pharmacy", use_container_width=True)

            if submitted:
                if not all([name, email, phone, location, region]):
                    st.error("Please fill in all required fields")
                elif not validate_email(email):
                    st.error("Invalid email format")
                elif not validate_phone(phone):
                    st.error("Invalid phone format")
                else:
                    pharmacy = {
                        'id': generate_id('PHARM'),
                        'name': name,
                        'email': email,
                        'phone': phone,
                        'location': location,
                        'pharmacy_type': pharmacy_type,
                        'region': region,
                        'created_at': datetime.now().isoformat()
                    }

                    st.session_state.pharmacies.append(pharmacy)
                    st.success(f"Pharmacy added: {pharmacy['id']}")

    with tab2:
        st.subheader("All Pharmacies")
        if st.session_state.pharmacies:
            st.dataframe(st.session_state.pharmacies, use_container_width=True)
            st.write(f"Total: {len(st.session_state.pharmacies)} pharmacies")
        else:
            st.info("No pharmacies added yet")

# Send Alerts Page
elif page == "Send Alerts":
    st.header("Send Alerts")

    if not st.session_state.pharmacies:
        st.warning("Please add pharmacies first")
    elif not st.session_state.drug_reports:
        st.warning("Please create a drug report first")
    else:
        alert_type = st.radio("Alert Type", ["Broadcast", "Targeted"])

        drug_report_idx = st.selectbox(
            "Select Drug Report",
            range(len(st.session_state.drug_reports)),
            format_func=lambda
                i: f"{st.session_state.drug_reports[i]['drug_name']} ({st.session_state.drug_reports[i]['severity']})"
        )

        drug_report = st.session_state.drug_reports[drug_report_idx]

        if alert_type == "Broadcast":
            st.info(f"This alert will be sent to all {len(st.session_state.pharmacies)} pharmacies")
            if st.button("Send Broadcast Alert", use_container_width=True):
                with st.spinner("Sending alerts..."):
                    results = st.session_state.broadcast_agent.send_alert(
                        drug_report,
                        st.session_state.pharmacies
                    )

                    st.session_state.delivery_receipts.extend(results['deliveries'])

                    st.success("Broadcast alerts sent!")
                    st.json(create_alert_summary(drug_report, results))

        else:  # Targeted
            col1, col2 = st.columns(2)

            available_regions = list(set([p['region'] for p in st.session_state.pharmacies]))
            available_types = list(set([p['pharmacy_type'] for p in st.session_state.pharmacies]))

            with col1:
                target_region = st.multiselect(
                    "Target Regions",
                    available_regions,
                    default=available_regions[:1] if available_regions else []
                )

            with col2:
                target_type = st.multiselect(
                    "Target Pharmacy Types",
                    available_types,
                    default=available_types[:1] if available_types else []
                )

            matching_count = len([p for p in st.session_state.pharmacies
                                  if (not target_region or p['region'] in target_region) and
                                  (not target_type or p['pharmacy_type'] in target_type)])

            st.info(f"This alert will be sent to {matching_count} matching pharmacies")

            if st.button("Send Targeted Alert", use_container_width=True):
                criteria = {}
                if target_region:
                    criteria['regions_affected'] = target_region
                if target_type:
                    criteria['pharmacy_type'] = target_type

                with st.spinner("Sending targeted alerts..."):
                    results = st.session_state.targeted_agent.send_alert(
                        drug_report,
                        st.session_state.pharmacies,
                        criteria
                    )

                    st.session_state.delivery_receipts.extend(results['deliveries'])

                    st.success("Targeted alerts sent!")
                    st.json(create_alert_summary(drug_report, results))

# Track Deliveries Page
elif page == "Track Deliveries":
    st.header("Track Deliveries")

    if st.session_state.delivery_receipts:
        # Convert to list of dicts for display
        receipts_list = []
        for delivery in st.session_state.delivery_receipts:
            if isinstance(delivery, dict):
                receipts_list.append(delivery)

        st.dataframe(receipts_list, use_container_width=True)

        st.divider()

        # Filter by status
        status_filter = st.selectbox("Filter by Status", ["All", "Sent", "Acknowledged", "Failed"])

        if status_filter != "All":
            filtered = [r for r in receipts_list if r.get('status') == status_filter.lower()]
            st.dataframe(filtered, use_container_width=True)
            st.write(f"Found {len(filtered)} deliveries with status: {status_filter}")
    else:
        st.info("No deliveries to track. Send an alert to get started!")

# Statistics Page
elif page == "Statistics":
    st.header("Statistics")

    if st.session_state.delivery_receipts:
        receipts_list = [d for d in st.session_state.delivery_receipts if isinstance(d, dict)]
        stats = calculate_acknowledgment_rate(receipts_list)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Deliveries", stats['total_receipts'])

        with col2:
            st.metric("Acknowledged", f"{stats['acknowledgment_rate']:.1f}%")

        with col3:
            st.metric("Pending", f"{stats['pending_rate']:.1f}%")

        with col4:
            st.metric("Failed", f"{stats['failure_rate']:.1f}%")

        st.divider()

        # Pie chart
        col1, col2 = st.columns(2)

        with col1:
            import plotly.graph_objects as go

            fig = go.Figure(data=[go.Pie(
                labels=['Acknowledged', 'Pending', 'Failed'],
                values=[
                    stats['acknowledged'],
                    stats['pending'],
                    stats['failed']
                ],
                marker=dict(colors=['#00CC00', '#FFCC00', '#FF0000'])
            )])
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Detailed Stats")
            for key, value in stats.items():
                if isinstance(value, float):
                    st.write(f"{key}: {value:.2f}{'%' if 'rate' in key else ''}")
                else:
                    st.write(f"{key}: {value}")
    else:
        st.info("No delivery data available yet. Send some alerts to see statistics!")

# Footer
st.divider()
st.markdown("""
---
**Drug Reporter** © 2024 | Multi-Agent Healthcare Safety System
""")