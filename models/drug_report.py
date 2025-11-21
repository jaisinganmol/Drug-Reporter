# models/drug_report.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class DrugReport:
    """Data model for drug safety reports"""

    id: str
    drug_name: str
    alert_type: str  # e.g., "Recall", "Safety Warning", "Contraindication"
    severity: str  # e.g., "Critical", "High", "Medium", "Low"
    description: str
    action_required: str
    created_at: str
    created_by: str
    updated_at: Optional[str] = None
    updated_by: Optional[str] = None
    expiration_date: Optional[str] = None
    affected_batches: Optional[list] = None
    manufacturer: Optional[str] = None
    regions_affected: Optional[list] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'DrugReport':
        """Create DrugReport from dictionary"""
        return cls(
            id=data.get('id'),
            drug_name=data.get('drug_name'),
            alert_type=data.get('alert_type'),
            severity=data.get('severity'),
            description=data.get('description'),
            action_required=data.get('action_required'),
            created_at=data.get('created_at', datetime.now().isoformat()),
            created_by=data.get('created_by'),
            updated_at=data.get('updated_at'),
            updated_by=data.get('updated_by'),
            expiration_date=data.get('expiration_date'),
            affected_batches=data.get('affected_batches'),
            manufacturer=data.get('manufacturer'),
            regions_affected=data.get('regions_affected')
        )

    def to_dict(self) -> dict:
        """Convert DrugReport to dictionary"""
        return {
            'id': self.id,
            'drug_name': self.drug_name,
            'alert_type': self.alert_type,
            'severity': self.severity,
            'description': self.description,
            'action_required': self.action_required,
            'created_at': self.created_at,
            'created_by': self.created_by,
            'updated_at': self.updated_at,
            'updated_by': self.updated_by,
            'expiration_date': self.expiration_date,
            'affected_batches': self.affected_batches,
            'manufacturer': self.manufacturer,
            'regions_affected': self.regions_affected
        }

    def is_expired(self) -> bool:
        """Check if alert has expired"""
        if not self.expiration_date:
            return False
        expiry = datetime.fromisoformat(self.expiration_date)
        return datetime.now() > expiry

    def get_severity_level(self) -> int:
        """Get numeric severity level for comparison"""
        severity_map = {
            'critical': 4,
            'high': 3,
            'medium': 2,
            'low': 1
        }
        return severity_map.get(self.severity.lower(), 0)

    def __str__(self) -> str:
        return f"DrugReport(id={self.id}, drug={self.drug_name}, severity={self.severity})"