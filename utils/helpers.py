# utils/helpers.py
import re
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_id(prefix: str = "") -> str:
    """
    Generate a unique ID with optional prefix

    Args:
        prefix: Optional prefix for the ID

    Returns:
        Unique identifier string
    """
    unique_id = str(uuid.uuid4())[:8].upper()
    if prefix:
        return f"{prefix}-{unique_id}"
    return unique_id


def validate_email(email: str) -> bool:
    """
    Validate email address format

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format

    Args:
        phone: Phone number to validate

    Returns:
        True if valid, False otherwise
    """
    # Remove common separators and spaces
    cleaned = re.sub(r'[\s\-\(\)\.]+', '', phone)

    # Check if it's 10+ digits
    pattern = r'^\+?1?\d{10,}$'
    return re.match(pattern, cleaned) is not None


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Format datetime to ISO format string

    Args:
        dt: Datetime object (uses current time if None)

    Returns:
        Formatted timestamp string
    """
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()


def parse_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Parse ISO format timestamp string to datetime

    Args:
        timestamp_str: ISO format timestamp string

    Returns:
        Datetime object or None if parsing fails
    """
    try:
        return datetime.fromisoformat(timestamp_str)
    except (ValueError, TypeError):
        logger.warning(f"Failed to parse timestamp: {timestamp_str}")
        return None


def sanitize_input(user_input: str) -> str:
    """
    Sanitize user input to prevent injection attacks

    Args:
        user_input: Raw user input

    Returns:
        Sanitized input string
    """
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>\"\'`]', '', user_input)
    # Remove extra whitespace
    sanitized = ' '.join(sanitized.split())
    return sanitized.strip()


def get_current_timestamp() -> str:
    """
    Get current timestamp in ISO format

    Returns:
        Current timestamp string
    """
    return datetime.now().isoformat()


def log_message(level: str, message: str, **kwargs) -> None:
    """
    Log a message with specified level

    Args:
        level: Log level ('info', 'warning', 'error', 'debug')
        message: Message to log
        **kwargs: Additional context to include
    """
    context = ' | '.join([f"{k}={v}" for k, v in kwargs.items()])
    full_message = f"{message} | {context}" if context else message

    if level.lower() == 'info':
        logger.info(full_message)
    elif level.lower() == 'warning':
        logger.warning(full_message)
    elif level.lower() == 'error':
        logger.error(full_message)
    elif level.lower() == 'debug':
        logger.debug(full_message)
    else:
        logger.info(full_message)


def create_alert_summary(drug_report: Dict, delivery_results: Dict) -> Dict:
    """
    Create a summary of an alert and its delivery

    Args:
        drug_report: Drug report dictionary
        delivery_results: Delivery results dictionary

    Returns:
        Summary dictionary
    """
    total_sent = len(delivery_results.get('deliveries', []))
    success_count = len([d for d in delivery_results.get('deliveries', [])
                         if d.get('status') == 'sent'])
    failure_count = len([d for d in delivery_results.get('deliveries', [])
                         if d.get('status') == 'failed'])

    return {
        'drug_name': drug_report.get('drug_name'),
        'alert_type': drug_report.get('alert_type'),
        'severity': drug_report.get('severity'),
        'agent_type': delivery_results.get('agent_type'),
        'timestamp': delivery_results.get('timestamp'),
        'total_sent': total_sent,
        'successful': success_count,
        'failed': failure_count,
        'success_rate': (success_count / total_sent * 100) if total_sent > 0 else 0,
        'target_criteria': delivery_results.get('target_criteria')
    }


def calculate_acknowledgment_rate(delivery_receipts: List[Dict]) -> Dict:
    """
    Calculate acknowledgment statistics from delivery receipts

    Args:
        delivery_receipts: List of delivery receipt dictionaries

    Returns:
        Dictionary with acknowledgment statistics
    """
    total = len(delivery_receipts)

    if total == 0:
        return {
            'total_receipts': 0,
            'acknowledged': 0,
            'pending': 0,
            'failed': 0,
            'acknowledgment_rate': 0.0,
            'pending_rate': 0.0,
            'failure_rate': 0.0
        }

    acknowledged = len([r for r in delivery_receipts if r.get('status') == 'acknowledged'])
    pending = len([r for r in delivery_receipts if r.get('status') == 'pending'])
    failed = len([r for r in delivery_receipts if r.get('status') == 'failed'])

    return {
        'total_receipts': total,
        'acknowledged': acknowledged,
        'pending': pending,
        'failed': failed,
        'acknowledgment_rate': (acknowledged / total * 100),
        'pending_rate': (pending / total * 100),
        'failure_rate': (failed / total * 100)
    }


def get_severity_color(severity: str) -> str:
    """
    Get color code for severity level (for UI purposes)

    Args:
        severity: Severity level

    Returns:
        Color code or name
    """
    severity_colors = {
        'critical': '#FF0000',  # Red
        'high': '#FF6600',  # Orange
        'medium': '#FFCC00',  # Yellow
        'low': '#00CC00'  # Green
    }
    return severity_colors.get(severity.lower(), '#808080')  # Gray default


def format_delivery_report(delivery_results: Dict) -> str:
    """
    Format delivery results into a readable report string

    Args:
        delivery_results: Delivery results dictionary

    Returns:
        Formatted report string
    """
    report = f"""
{'=' * 60}
DELIVERY REPORT
{'=' * 60}
Agent Type: {delivery_results.get('agent_type')}
Timestamp: {delivery_results.get('timestamp')}
Drug Name: {delivery_results.get('drug_name')}
Total Pharmacies: {delivery_results.get('total_pharmacies')}

Results:
  - Successful: {delivery_results.get('success_count', 0)}
  - Failed: {delivery_results.get('failure_count', 0)}

Target Criteria: {delivery_results.get('target_criteria')}
{'=' * 60}
    """
    return report


def export_to_csv(data: List[Dict], filename: str) -> bool:
    """
    Export data to CSV file

    Args:
        data: List of dictionaries to export
        filename: Output filename

    Returns:
        True if successful, False otherwise
    """
    try:
        import csv

        if not data:
            logger.warning("No data to export")
            return False

        keys = data[0].keys()

        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(data)

        logger.info(f"Data exported to {filename}")
        return True
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        return False


def import_from_csv(filename: str) -> Optional[List[Dict]]:
    """
    Import data from CSV file

    Args:
        filename: Input CSV filename

    Returns:
        List of dictionaries or None if import fails
    """
    try:
        import csv

        data = []
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            data = list(reader)

        logger.info(f"Data imported from {filename}")
        return data
    except Exception as e:
        logger.error(f"Error importing from CSV: {str(e)}")
        return None