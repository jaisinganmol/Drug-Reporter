# agents/base_agent.py
from abc import ABC, abstractmethod
from anthropic import Anthropic
from typing import List, Dict
import json
from datetime import datetime


class BaseAgent(ABC):
    """Base class for all drug alert agents"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = Anthropic(api_key=api_key)
        self.model = "claude-sonnet-4-20250514"
        self.delivery_receipts = []

    @abstractmethod
    def send_alert(self, drug_report: Dict, pharmacies: List[Dict]) -> Dict:
        """
        Send alert to pharmacies. Must be implemented by subclasses.

        Args:
            drug_report: Dictionary containing drug safety information
            pharmacies: List of pharmacy dictionaries

        Returns:
            Dictionary with delivery status
        """
        pass

    def _create_message(self, drug_report: Dict, pharmacy: Dict) -> str:
        """Create formatted alert message for a pharmacy"""
        return f"""
        DRUG SAFETY ALERT

        Pharmacy: {pharmacy['name']}
        Drug: {drug_report['drug_name']}
        Alert Type: {drug_report['alert_type']}
        Severity: {drug_report['severity']}

        Description:
        {drug_report['description']}

        Action Required:
        {drug_report['action_required']}

        Please acknowledge receipt of this alert.
        """

    def track_delivery(self, receipt_id: str) -> Dict:
        """Track delivery status of a specific receipt"""
        receipt = next((r for r in self.delivery_receipts if r['id'] == receipt_id), None)
        if receipt:
            return {
                'status': 'found',
                'receipt': receipt
            }
        return {
            'status': 'not_found',
            'message': f'Receipt {receipt_id} not found'
        }

    def process_acknowledgment(self, pharmacy_id: str, receipt_id: str) -> Dict:
        """Process acknowledgment from a pharmacy"""
        receipt = next((r for r in self.delivery_receipts
                        if r['id'] == receipt_id and r['pharmacy_id'] == pharmacy_id), None)

        if receipt:
            receipt['status'] = 'acknowledged'
            receipt['acknowledged_at'] = datetime.now().isoformat()
            return {
                'success': True,
                'message': f'Acknowledgment processed for {pharmacy_id}'
            }

        return {
            'success': False,
            'message': 'Receipt not found or already acknowledged'
        }

    def get_pending_receipts(self) -> List[Dict]:
        """Get all receipts that haven't been acknowledged"""
        return [r for r in self.delivery_receipts if r['status'] == 'pending']

    def get_acknowledged_receipts(self) -> List[Dict]:
        """Get all acknowledged receipts"""
        return [r for r in self.delivery_receipts if r['status'] == 'acknowledged']

    def get_delivery_statistics(self) -> Dict:
        """Get statistics about deliveries"""
        total = len(self.delivery_receipts)
        acknowledged = len(self.get_acknowledged_receipts())
        pending = len(self.get_pending_receipts())

        return {
            'total_sent': total,
            'acknowledged': acknowledged,
            'pending': pending,
            'acknowledgment_rate': (acknowledged / total * 100) if total > 0 else 0
        }

    def _generate_receipt_id(self) -> str:
        """Generate unique receipt ID"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"RECEIPT-{timestamp}-{len(self.delivery_receipts)}"

    def _call_claude(self, system_prompt: str, user_message: str) -> str:
        """Make API call to Claude"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            return message.content[0].text
        except Exception as e:
            return f"Error calling Claude API: {str(e)}"