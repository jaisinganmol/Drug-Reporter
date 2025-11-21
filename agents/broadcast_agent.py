# agents/broadcast_agent.py
from typing import List, Dict
from datetime import datetime
from .base_agent import BaseAgent


class BroadcastAgent(BaseAgent):
    """Agent for broadcasting alerts to all pharmacies"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.agent_type = "broadcast"

    def send_alert(self, drug_report: Dict, pharmacies: List[Dict]) -> Dict:
        """
        Send alert to ALL pharmacies in the list

        Args:
            drug_report: Drug safety information
            pharmacies: List of all pharmacies

        Returns:
            Dictionary with delivery results
        """
        results = {
            'agent_type': 'broadcast',
            'timestamp': datetime.now().isoformat(),
            'drug_name': drug_report['drug_name'],
            'total_pharmacies': len(pharmacies),
            'deliveries': []
        }

        system_prompt = """You are a drug safety alert system. Your role is to 
        communicate critical drug safety information to pharmacies clearly and 
        professionally. Ensure all important details are conveyed."""

        for pharmacy in pharmacies:
            try:
                # Create the alert message
                alert_message = self._create_message(drug_report, pharmacy)

                # Send via Claude AI
                response = self._call_claude(system_prompt, alert_message)

                # Create delivery receipt
                receipt_id = self._generate_receipt_id()
                receipt = {
                    'id': receipt_id,
                    'pharmacy_id': pharmacy['id'],
                    'pharmacy_name': pharmacy['name'],
                    'drug_name': drug_report['drug_name'],
                    'sent_at': datetime.now().isoformat(),
                    'status': 'pending',
                    'acknowledged_at': None,
                    'agent_type': 'broadcast'
                }

                self.delivery_receipts.append(receipt)

                results['deliveries'].append({
                    'pharmacy': pharmacy['name'],
                    'status': 'sent',
                    'receipt_id': receipt_id,
                    'response': response[:100] + '...' if len(response) > 100 else response
                })

            except Exception as e:
                results['deliveries'].append({
                    'pharmacy': pharmacy['name'],
                    'status': 'failed',
                    'error': str(e)
                })

        results['success_count'] = len([d for d in results['deliveries'] if d['status'] == 'sent'])
        results['failure_count'] = len([d for d in results['deliveries'] if d['status'] == 'failed'])

        return results

    def send_follow_up(self, receipt_ids: List[str]) -> Dict:
        """
        Send follow-up reminders to pharmacies that haven't acknowledged

        Args:
            receipt_ids: List of receipt IDs to follow up on

        Returns:
            Dictionary with follow-up results
        """
        results = {
            'follow_ups_sent': 0,
            'already_acknowledged': 0,
            'not_found': 0,
            'details': []
        }

        for receipt_id in receipt_ids:
            receipt = next((r for r in self.delivery_receipts if r['id'] == receipt_id), None)

            if not receipt:
                results['not_found'] += 1
                results['details'].append({
                    'receipt_id': receipt_id,
                    'status': 'not_found'
                })
                continue

            if receipt['status'] == 'acknowledged':
                results['already_acknowledged'] += 1
                results['details'].append({
                    'receipt_id': receipt_id,
                    'pharmacy': receipt['pharmacy_name'],
                    'status': 'already_acknowledged'
                })
                continue

            # Send follow-up
            system_prompt = "Send a polite follow-up reminder about an unacknowledged drug safety alert."
            follow_up_message = f"""
            FOLLOW-UP REMINDER

            Pharmacy: {receipt['pharmacy_name']}
            Original Alert: {receipt['drug_name']}
            Sent: {receipt['sent_at']}

            We have not yet received acknowledgment of this critical drug safety alert.
            Please confirm receipt as soon as possible.

            Receipt ID: {receipt_id}
            """

            response = self._call_claude(system_prompt, follow_up_message)
            results['follow_ups_sent'] += 1
            results['details'].append({
                'receipt_id': receipt_id,
                'pharmacy': receipt['pharmacy_name'],
                'status': 'follow_up_sent'
            })

        return results