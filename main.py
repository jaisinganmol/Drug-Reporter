# main.py
import os
import json
from dotenv import load_dotenv
from agents import AgentFactory
from models import DrugReport, Pharmacy, DeliveryReceipt
from utils import (
    generate_id,
    log_message,
    create_alert_summary,
    calculate_acknowledgment_rate,
    format_delivery_report
)

# Load environment variables
load_dotenv()
API_KEY = os.getenv('ANTHROPIC_API_KEY')

if not API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not found in .env file")


class DrugReporterCLI:
    """Main CLI orchestrator for Drug Reporter system"""

    def __init__(self):
        self.agent_factory = AgentFactory()
        self.pharmacies = []
        self.drug_reports = []
        self.broadcast_agent = None
        self.targeted_agent = None
        self.initialize_agents()

    def initialize_agents(self):
        """Initialize both broadcast and targeted agents"""
        try:
            self.broadcast_agent = self.agent_factory.create_agent('broadcast', API_KEY)
            self.targeted_agent = self.agent_factory.create_agent('targeted', API_KEY)
            log_message('info', 'Agents initialized successfully')
        except Exception as e:
            log_message('error', 'Failed to initialize agents', error=str(e))
            raise

    def add_sample_pharmacies(self):
        """Add sample pharmacies for testing"""
        sample_pharmacies = [
            {
                'id': generate_id('PHARM'),
                'name': 'Downtown Pharmacy',
                'location': 'New York',
                'phone': '555-0001',
                'email': 'downtown@pharmacy.com',
                'pharmacy_type': 'Independent',
                'region': 'Northeast'
            },
            {
                'id': generate_id('PHARM'),
                'name': 'Main Street Pharmacy',
                'location': 'New York',
                'phone': '555-0002',
                'email': 'mainst@pharmacy.com',
                'pharmacy_type': 'Chain',
                'region': 'Northeast'
            },
            {
                'id': generate_id('PHARM'),
                'name': 'West Side Pharmacy',
                'location': 'Los Angeles',
                'phone': '555-0003',
                'email': 'westside@pharmacy.com',
                'pharmacy_type': 'Independent',
                'region': 'West'
            },
            {
                'id': generate_id('PHARM'),
                'name': 'Central Pharmacy',
                'location': 'Chicago',
                'phone': '555-0004',
                'email': 'central@pharmacy.com',
                'pharmacy_type': 'Chain',
                'region': 'Midwest'
            }
        ]

        self.pharmacies = sample_pharmacies
        log_message('info', 'Sample pharmacies added', count=len(sample_pharmacies))

    def create_sample_drug_report(self) -> dict:
        """Create a sample drug report"""
        report = {
            'id': generate_id('DRUG'),
            'drug_name': 'Metformin XR 500mg',
            'alert_type': 'Safety Warning',
            'severity': 'High',
            'description': 'Potential contamination detected in batch numbers 12345-12500. Affected batches may contain glass particles.',
            'action_required': 'Immediately notify all patients. Recall all affected batches. Check inventory against batch numbers.',
            'created_at': __import__('datetime').datetime.now().isoformat(),
            'created_by': 'FDA Safety Team',
            'manufacturer': 'Pharma Corp Inc.',
            'affected_batches': ['12345-12500'],
            'regions_affected': ['Northeast', 'Midwest']
        }
        return report

    def send_broadcast_alert(self, drug_report: dict):
        """Send alert to all pharmacies"""
        log_message('info', 'Starting broadcast alert', drug=drug_report['drug_name'])

        try:
            results = self.broadcast_agent.send_alert(drug_report, self.pharmacies)

            # Print results
            print(format_delivery_report(results))

            # Create summary
            summary = create_alert_summary(drug_report, results)
            log_message('info', 'Broadcast alert completed', summary=json.dumps(summary, indent=2))

            return results
        except Exception as e:
            log_message('error', 'Broadcast alert failed', error=str(e))
            raise

    def send_targeted_alert(self, drug_report: dict, criteria: dict):
        """Send alert to specific pharmacies based on criteria"""
        log_message('info', 'Starting targeted alert', drug=drug_report['drug_name'], criteria=criteria)

        try:
            results = self.targeted_agent.send_alert(drug_report, self.pharmacies, criteria)

            # Print results
            print(format_delivery_report(results))

            # Create summary
            summary = create_alert_summary(drug_report, results)
            log_message('info', 'Targeted alert completed', summary=json.dumps(summary, indent=2))

            return results
        except Exception as e:
            log_message('error', 'Targeted alert failed', error=str(e))
            raise

    def get_delivery_statistics(self):
        """Get overall delivery statistics"""
        all_receipts = (
                self.broadcast_agent.delivery_receipts +
                self.targeted_agent.delivery_receipts
        )

        stats = calculate_acknowledgment_rate(all_receipts)

        print("\n" + "=" * 60)
        print("DELIVERY STATISTICS")
        print("=" * 60)
        print(f"Total Receipts: {stats['total_receipts']}")
        print(f"Acknowledged: {stats['acknowledged']} ({stats['acknowledgment_rate']:.1f}%)")
        print(f"Pending: {stats['pending']} ({stats['pending_rate']:.1f}%)")
        print(f"Failed: {stats['failed']} ({stats['failure_rate']:.1f}%)")
        print("=" * 60 + "\n")

        return stats

    def send_follow_ups(self):
        """Send follow-up reminders to pending pharmacies"""
        pending_receipts = self.broadcast_agent.get_pending_receipts()
        pending_ids = [r['id'] for r in pending_receipts]

        if not pending_ids:
            log_message('info', 'No pending receipts for follow-up')
            print("No pending receipts found.\n")
            return

        log_message('info', 'Sending follow-ups', count=len(pending_ids))
        results = self.broadcast_agent.send_follow_up(pending_ids)

        print("\n" + "=" * 60)
        print("FOLLOW-UP RESULTS")
        print("=" * 60)
        print(f"Follow-ups sent: {results['follow_ups_sent']}")
        print(f"Already acknowledged: {results['already_acknowledged']}")
        print(f"Not found: {results['not_found']}")
        print("=" * 60 + "\n")

    def run_demo(self):
        """Run a complete demo of the system"""
        print("\n" + "=" * 60)
        print("DRUG REPORTER - MULTI-AGENT SYSTEM DEMO")
        print("=" * 60 + "\n")

        # Setup
        print("Step 1: Loading pharmacies...")
        self.add_sample_pharmacies()
        print(f"✓ Loaded {len(self.pharmacies)} pharmacies\n")

        # Create drug report
        print("Step 2: Creating drug safety report...")
        drug_report = self.create_sample_drug_report()
        print(f"✓ Created report for: {drug_report['drug_name']}\n")

        # Send broadcast alert
        print("Step 3: Sending broadcast alert to all pharmacies...")
        self.send_broadcast_alert(drug_report)

        # Send targeted alert
        print("Step 4: Sending targeted alert to specific regions...")
        targeted_criteria = {
            'regions_affected': ['Northeast', 'Midwest']
        }
        self.send_targeted_alert(drug_report, targeted_criteria)

        # Get statistics
        print("Step 5: Retrieving delivery statistics...")
        self.get_delivery_statistics()

        # Send follow-ups
        print("Step 6: Sending follow-up reminders...")
        self.send_follow_ups()

        # Final statistics
        print("Step 7: Final delivery statistics...")
        self.get_delivery_statistics()

        print("=" * 60)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60 + "\n")


def main():
    """Main entry point"""
    try:
        cli = DrugReporterCLI()
        cli.run_demo()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        log_message('error', 'Fatal error in main', error=str(e))
        print(f"Error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()