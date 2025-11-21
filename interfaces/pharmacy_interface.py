# interfaces/pharmacy_interface.py
from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class PharmacyInterface(ABC):
    """Interface for pharmacy management operations"""

    @abstractmethod
    def add_pharmacy(self, pharmacy: Dict) -> bool:
        """
        Add a new pharmacy to the system

        Args:
            pharmacy: Dictionary containing pharmacy information

        Returns:
            True if added successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_pharmacy(self, pharmacy_id: str) -> Optional[Dict]:
        """
        Retrieve a pharmacy by ID

        Args:
            pharmacy_id: Unique pharmacy identifier

        Returns:
            Pharmacy dictionary or None if not found
        """
        pass

    @abstractmethod
    def get_all_pharmacies(self) -> List[Dict]:
        """
        Retrieve all pharmacies

        Returns:
            List of pharmacy dictionaries
        """
        pass

    @abstractmethod
    def update_pharmacy(self, pharmacy_id: str, updates: Dict) -> bool:
        """
        Update pharmacy information

        Args:
            pharmacy_id: Unique pharmacy identifier
            updates: Dictionary with fields to update

        Returns:
            True if updated successfully, False otherwise
        """
        pass

    @abstractmethod
    def remove_pharmacy(self, pharmacy_id: str) -> bool:
        """
        Remove a pharmacy from the system

        Args:
            pharmacy_id: Unique pharmacy identifier

        Returns:
            True if removed successfully, False otherwise
        """
        pass