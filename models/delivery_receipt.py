# models/delivery_receipt.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class DeliveryReceipt:
    """Data model for delivery tracking"""

    id: str
    pharmacy_id: str
    pharmacy_name: str
    drug_name: str
    sent_at: str
    status: str  # e.g., "pending", "acknowledged", "failed"
    agent_type: str  # e.g., "broadcast", "targeted"
    acknowledged_at: Optional[str] = None
    failed_at: Optional[str] = None
    failure_reason: Optional[str] = None
    attempts: int = 1
    max_attempts: int = 3
    target_criteria: Optional[dict] = None
    response_message: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> 'DeliveryReceipt':
        """Create DeliveryReceipt from dictionary"""
        return cls(
            id=data.get('id'),
            pharmacy_id=data.get('pharmacy_id'),
            pharmacy_name=data.get('pharmacy_name'),
            drug_name=data.get('drug_name'),
            sent_at=data.get('sent_at', datetime.now().isoformat()),
            status=data.get('status', 'pending'),
            agent_type=data.get('agent_type'),
            acknowledged_at=data.get('acknowledged_at'),
            failed_at=data.get('failed_at'),
            failure_reason=data.get('failure_reason'),
            attempts=data.get('attempts', 1),
            max_attempts=data.get('max_attempts', 3),
            target_criteria=data.get('target_criteria'),
            response_message=data.get('response_message')
        )

    def to_dict(self) -> dict:
        """Convert DeliveryReceipt to dictionary"""
        return {
            'id': self.id,
            'pharmacy_id': self.pharmacy_id,
            'pharmacy_name': self.pharmacy_name,
            'drug_name': self.drug_name,
            'sent_at': self.sent_at,
            'status': self.status,
            'agent_type': self.agent_type,
            'acknowledged_at': self.acknowledged_at,
            'failed_at': self.failed_at,
            'failure_reason': self.failure_reason,
            'attempts': self.attempts,
            'max_attempts': self.max_attempts,
            'target_criteria': self.target_criteria,
            'response_message': self.response_message
        }

    def mark_acknowledged(self) -> None:
        """Mark receipt as acknowledged"""
        self.status = 'acknowledged'
        self.acknowledged_at = datetime.now().isoformat()

    def mark_failed(self, reason: str) -> None:
        """Mark receipt as failed with reason"""
        self.failed_at = datetime.now().isoformat()
        self.failure_reason = reason
        if self.attempts >= self.max_attempts:
            self.status = 'failed'
        else:
            self.status = 'retry_pending'

    def increment_attempts(self) -> bool:
        """Increment attempts and return if retry should continue"""
        self.attempts += 1
        return self.attempts < self.max_attempts

    def is_pending(self) -> bool:
        """Check if receipt is still pending"""
        return self.status == 'pending'

    def is_acknowledged(self) -> bool:
        """Check if receipt has been acknowledged"""
        return self.status == 'acknowledged'

    def is_failed(self) -> bool:
        """Check if delivery has failed"""
        return self.status == 'failed'

    def can_retry(self) -> bool:
        """Check if delivery can be retried"""
        return self.attempts < self.max_attempts and self.status in ['retry_pending', 'failed']

    def get_delivery_time_minutes(self) -> Optional[float]:
        """Get time between sent and acknowledged in minutes"""
        if not self.acknowledged_at:
            return None
        sent = datetime.fromisoformat(self.sent_at)
        acknowledged = datetime.fromisoformat(self.acknowledged_at)
        return (acknowledged - sent).total_seconds() / 60

    def __str__(self) -> str:
        return f"DeliveryReceipt(id={self.id}, pharmacy={self.pharmacy_name}, status={self.status})"