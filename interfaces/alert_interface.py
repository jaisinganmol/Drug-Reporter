# interfaces/alert_interface.py
from abc import ABC, abstractmethod
from typing import List, Dict


class AlertInterface(ABC):
    """Interface for alert sending operations"""

    @abstractmethod
    def send_alert(self, drug_report: Dict, pharmacies: List[Dict]) -> Dict:
        """
        Send alert to pharmacies

        Args:
            drug_report: Dictionary containing drug safety information
            pharmacies: List of pharmacy dictionaries

        Returns:
            Dictionary with delivery status and results
        """
        pass

    @abstractmethod
    def track_delivery(self, receipt_id: str) -> Dict:
        """
        Track delivery status of a specific receipt

        Args:
            receipt_id: Unique receipt identifier

        Returns:
            Dictionary with tracking information
        """
        pass

    @abstractmethod
    def get_delivery_statistics(self) -> Dict:
        """
        Get statistics about deliveries

        Returns:
            Dictionary with delivery statistics
        """
        pass