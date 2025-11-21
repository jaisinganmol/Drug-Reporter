# agents/targeted_agent.py
from typing import List, Dict
from datetime import datetime
from .base_agent import BaseAgent


class TargetedAgent(BaseAgent):
    """Agent for sending targeted alerts to specific pharmacies"""

    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.agent_type = "targeted"

    def send_alert(self, drug_report: Dict, pharmacies: List[Dict],
                   target_criteria: Dict = None) -> Dict:
        """
        Send alert to SPECIFIC pharmacies based on criteria

        Args:
            drug_report: Drug safety information
            pharmacies: List of pharmacies to filter from
            target_criteria: Criteria for targeting (location, type, etc.)

        Returns:
            Dictionary with delivery results
        """
        # Filter pharmacies based on criteria
        targeted_pharmacies = self._filter_pharmacies(pharmacies, target_criteria)

        results = {
            'agent_type': 'targeted',
            'timestamp': datetime.now().isoformat(),
            'drug_name': drug_report['drug_name'],
            'target_criteria': target_criteria,
            'total_available': len(pharmacies),
            'targeted_count': len(targeted_pharmacies),
            'deliveries': []
        }

        if not targeted_pharmacies:
            results['message'] = 'No pharmacies matched the target criteria'
            return results

        system_prompt = f"""You are a targeted drug safety alert system. 
        This alert is being sent to specific pharmacies that meet certain criteria: 
        {target_criteria}. Communicate the critical drug safety information clearly."""

        for pharmacy in targeted_pharmacies:
            try:
                # Create personalized alert
                alert_message = self._create_targeted_message(drug_report, pharmacy, target_criteria)

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
                    'agent_type': 'targeted',
                    'target_criteria': target_criteria
                }

                self.delivery_receipts.append(receipt)

                results['deliveries'].append({
                    'pharmacy': pharmacy['name'],
                    'status': 'sent',
                    'receipt_id': receipt_id,
                    'matched_criteria': self._get_matching_criteria(pharmacy, target_criteria),
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

    def _filter_pharmacies(self, pharmacies: List[Dict], criteria: Dict) -> List[Dict]:
        """Filter pharmacies based on targeting criteria"""
        if not criteria:
            return pharmacies

        filtered = pharmacies

        # Filter by location
        if 'regions_affected' in criteria and criteria['regions_affected']:
            regions = criteria['regions_affected']
            # Handle both string and list inputs
            if isinstance(regions, str):
                regions = [regions]
            filtered = [p for p in filtered
                        if p.get('region', '').lower() in [r.lower() for r in regions]]

        # Filter by pharmacy type
        if 'pharmacy_type' in criteria and criteria['pharmacy_type']:
            types = criteria['pharmacy_type']
            # Handle both string and list inputs
            if isinstance(types, str):
                types = [types]
            filtered = [p for p in filtered
                        if p.get('pharmacy_type', '').lower() in [t.lower() for t in types]]

        # Filter by location (alternative field name)
        if 'location' in criteria and criteria['location']:
            location = criteria['location']
            if isinstance(location, list):
                location = location[0] if location else None
            if location:
                filtered = [p for p in filtered
                            if p.get('location', '').lower() == location.lower()]

        # Filter by specific IDs
        if 'pharmacy_ids' in criteria and criteria['pharmacy_ids']:
            filtered = [p for p in filtered
                        if p['id'] in criteria['pharmacy_ids']]

        # Filter by region
        if 'region' in criteria and criteria['region']:
            region = criteria['region']
            if isinstance(region, list):
                region = region[0] if region else None
            if region:
                filtered = [p for p in filtered
                            if p.get('region', '').lower() == region.lower()]

        return filtered

    def _create_targeted_message(self, drug_report: Dict, pharmacy: Dict,
                                 criteria: Dict) -> str:
        """Create a targeted alert message with criteria explanation"""
        base_message = self._create_message(drug_report, pharmacy)

        targeting_reason = "\n\nTARGETING INFORMATION:\n"
        targeting_reason += "This alert has been sent to your pharmacy because:\n"

        if 'regions_affected' in criteria and criteria['regions_affected']:
            targeting_reason += f"- Region Match: {criteria['regions_affected']}\n"
        if 'pharmacy_type' in criteria and criteria['pharmacy_type']:
            targeting_reason += f"- Pharmacy Type: {criteria['pharmacy_type']}\n"
        if 'location' in criteria and criteria['location']:
            targeting_reason += f"- Location: {criteria['location']}\n"

        return base_message + targeting_reason

    def _get_matching_criteria(self, pharmacy: Dict, criteria: Dict) -> List[str]:
        """Get list of criteria that this pharmacy matched"""
        matches = []

        if 'regions_affected' in criteria and criteria['regions_affected']:
            regions = criteria['regions_affected']
            if isinstance(regions, str):
                regions = [regions]
            if pharmacy.get('region', '').lower() in [r.lower() for r in regions]:
                matches.append(f"region: {pharmacy.get('region')}")

        if 'pharmacy_type' in criteria and criteria['pharmacy_type']:
            types = criteria['pharmacy_type']
            if isinstance(types, str):
                types = [types]
            if pharmacy.get('pharmacy_type', '').lower() in [t.lower() for t in types]:
                matches.append(f"type: {pharmacy.get('pharmacy_type')}")

        if 'location' in criteria and pharmacy.get('location', '').lower() == criteria['location'].lower():
            matches.append(f"location: {criteria['location']}")

        if 'region' in criteria and pharmacy.get('region', '').lower() == criteria['region'].lower():
            matches.append(f"region: {criteria['region']}")

        if 'pharmacy_ids' in criteria and pharmacy['id'] in criteria['pharmacy_ids']:
            matches.append("specific ID match")

        return matches