# models/pharmacy.py
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime


@dataclass
class Pharmacy:
    """Data model for pharmacy information"""

    id: str
    name: str
    location: str
    phone: str
    email: str
    pharmacy_type: str  # e.g., "Chain", "Independent", "Hospital"
    region: str
    created_at: str
    is_active: bool = True
    manager_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    fax: Optional[str] = None
    hours_of_operation: Optional[str] = None
    contact_person: Optional[str] = None
    contact_person_email: Optional[str] = None
    contact_person_phone: Optional[str] = None
    previous_alerts_count: int = 0
    acknowledgment_rate: float = 0.0
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> 'Pharmacy':
        """Create Pharmacy from dictionary"""
        return cls(
            id=data.get('id'),
            name=data.get('name'),
            location=data.get('location'),
            phone=data.get('phone'),
            email=data.get('email'),
            pharmacy_type=data.get('pharmacy_type'),
            region=data.get('region'),
            created_at=data.get('created_at', datetime.now().isoformat()),
            is_active=data.get('is_active', True),
            manager_name=data.get('manager_name'),
            address=data.get('address'),
            city=data.get('city'),
            state=data.get('state'),
            zip_code=data.get('zip_code'),
            fax=data.get('fax'),
            hours_of_operation=data.get('hours_of_operation'),
            contact_person=data.get('contact_person'),
            contact_person_email=data.get('contact_person_email'),
            contact_person_phone=data.get('contact_person_phone'),
            previous_alerts_count=data.get('previous_alerts_count', 0),
            acknowledgment_rate=data.get('acknowledgment_rate', 0.0),
            tags=data.get('tags', [])
        )

    def to_dict(self) -> dict:
        """Convert Pharmacy to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'location': self.location,
            'phone': self.phone,
            'email': self.email,
            'pharmacy_type': self.pharmacy_type,
            'region': self.region,
            'created_at': self.created_at,
            'is_active': self.is_active,
            'manager_name': self.manager_name,
            'address': self.address,
            'city': self.city,
            'state': self.state,
            'zip_code': self.zip_code,
            'fax': self.fax,
            'hours_of_operation': self.hours_of_operation,
            'contact_person': self.contact_person,
            'contact_person_email': self.contact_person_email,
            'contact_person_phone': self.contact_person_phone,
            'previous_alerts_count': self.previous_alerts_count,
            'acknowledgment_rate': self.acknowledgment_rate,
            'tags': self.tags
        }

    def get_contact_info(self) -> dict:
        """Get primary contact information"""
        return {
            'name': self.contact_person or self.manager_name,
            'email': self.contact_person_email or self.email,
            'phone': self.contact_person_phone or self.phone,
            'fax': self.fax
        }

    def add_tag(self, tag: str) -> None:
        """Add a tag to the pharmacy"""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the pharmacy"""
        if tag in self.tags:
            self.tags.remove(tag)

    def has_tag(self, tag: str) -> bool:
        """Check if pharmacy has a specific tag"""
        return tag in self.tags

    def update_acknowledgment_rate(self, rate: float) -> None:
        """Update acknowledgment rate"""
        if 0 <= rate <= 100:
            self.acknowledgment_rate = rate

    def increment_alert_count(self) -> None:
        """Increment previous alerts count"""
        self.previous_alerts_count += 1

    def __str__(self) -> str:
        return f"Pharmacy(id={self.id}, name={self.name}, location={self.location})"