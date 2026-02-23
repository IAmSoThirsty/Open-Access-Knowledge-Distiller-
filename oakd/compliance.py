"""
Compliance and Regulatory Controls Module

Provides compliance tracking and regulatory reporting:
- GDPR compliance
- Data retention policies
- Consent management
- Export and deletion rights
- Compliance reporting
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class DataCategory(Enum):
    """Categories of data for compliance"""
    RESEARCH_DATA = "research_data"
    OPERATIONAL_DATA = "operational_data"
    AUDIT_DATA = "audit_data"
    PERSONAL_DATA = "personal_data"
    SYSTEM_DATA = "system_data"


class ProcessingPurpose(Enum):
    """Lawful purposes for data processing"""
    RESEARCH = "research"
    OPERATIONAL = "operational"
    AUDIT = "audit"
    LEGAL = "legal"
    CONSENT = "consent"


class DataSubjectRight(Enum):
    """Data subject rights under GDPR"""
    ACCESS = "access"  # Right to access
    RECTIFICATION = "rectification"  # Right to rectification
    ERASURE = "erasure"  # Right to be forgotten
    PORTABILITY = "portability"  # Right to data portability
    RESTRICTION = "restriction"  # Right to restriction
    OBJECTION = "objection"  # Right to object


@dataclass
class DataRetentionPolicy:
    """Data retention policy"""
    category: DataCategory
    retention_days: int
    deletion_method: str  # "secure_delete", "anonymize", "archive"
    legal_basis: str
    description: str

    def is_expired(self, creation_date: datetime) -> bool:
        """Check if data should be deleted based on retention period"""
        age = datetime.utcnow() - creation_date
        return age.days > self.retention_days


@dataclass
class ConsentRecord:
    """Record of user consent"""
    user_id: str
    purpose: ProcessingPurpose
    granted: bool
    timestamp: str
    consent_text: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            'user_id': self.user_id,
            'purpose': self.purpose.value,
            'granted': self.granted,
            'timestamp': self.timestamp,
            'consent_text': self.consent_text,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent
        }


@dataclass
class DataSubjectRequest:
    """Data subject access/deletion request"""
    request_id: str
    user_id: str
    right: DataSubjectRight
    timestamp: str
    status: str  # pending, in_progress, completed, rejected
    completion_date: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            'user_id': self.user_id,
            'right': self.right.value,
            'timestamp': self.timestamp,
            'status': self.status,
            'completion_date': self.completion_date,
            'notes': self.notes
        }


class ComplianceController:
    """
    Manages regulatory compliance.

    Features:
    - Data retention policies
    - Consent management
    - Data subject rights
    - Compliance reporting
    """

    def __init__(self, compliance_dir: str):
        """
        Initialize compliance controller.

        Args:
            compliance_dir: Directory for compliance records
        """
        self.compliance_dir = Path(compliance_dir)
        self.compliance_dir.mkdir(parents=True, exist_ok=True)

        self.consent_file = self.compliance_dir / "consents.jsonl"
        self.requests_file = self.compliance_dir / "dsr_requests.jsonl"

        self._retention_policies: Dict[DataCategory, DataRetentionPolicy] = {}
        self._initialize_default_policies()

    def _initialize_default_policies(self):
        """Initialize default retention policies"""
        # Research data - 7 years (typical academic retention)
        self.register_retention_policy(DataRetentionPolicy(
            category=DataCategory.RESEARCH_DATA,
            retention_days=365 * 7,
            deletion_method="archive",
            legal_basis="Research purposes with informed consent",
            description="Research documents and extracted knowledge"
        ))

        # Operational data - 1 year
        self.register_retention_policy(DataRetentionPolicy(
            category=DataCategory.OPERATIONAL_DATA,
            retention_days=365,
            deletion_method="secure_delete",
            legal_basis="Legitimate business interest",
            description="Processing logs and metrics"
        ))

        # Audit data - 7 years (regulatory requirement)
        self.register_retention_policy(DataRetentionPolicy(
            category=DataCategory.AUDIT_DATA,
            retention_days=365 * 7,
            deletion_method="archive",
            legal_basis="Legal obligation",
            description="Audit logs and security events"
        ))

        # Personal data - 1 year or until consent withdrawn
        self.register_retention_policy(DataRetentionPolicy(
            category=DataCategory.PERSONAL_DATA,
            retention_days=365,
            deletion_method="secure_delete",
            legal_basis="Consent",
            description="User personal information"
        ))

    def register_retention_policy(self, policy: DataRetentionPolicy):
        """Register data retention policy"""
        self._retention_policies[policy.category] = policy

    def get_retention_policy(self, category: DataCategory) -> Optional[DataRetentionPolicy]:
        """Get retention policy for data category"""
        return self._retention_policies.get(category)

    def record_consent(
        self,
        user_id: str,
        purpose: ProcessingPurpose,
        granted: bool,
        consent_text: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ConsentRecord:
        """
        Record user consent.

        Args:
            user_id: User identifier
            purpose: Processing purpose
            granted: Whether consent was granted
            consent_text: Full consent text shown to user
            ip_address: User IP address
            user_agent: User agent string

        Returns:
            ConsentRecord
        """
        record = ConsentRecord(
            user_id=user_id,
            purpose=purpose,
            granted=granted,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            consent_text=consent_text,
            ip_address=ip_address,
            user_agent=user_agent
        )

        # Append to consent log
        with open(self.consent_file, 'a') as f:
            f.write(json.dumps(record.to_dict()) + '\n')

        return record

    def check_consent(self, user_id: str, purpose: ProcessingPurpose) -> bool:
        """
        Check if user has granted consent for purpose.

        Args:
            user_id: User identifier
            purpose: Processing purpose

        Returns:
            True if consent granted, False otherwise
        """
        if not self.consent_file.exists():
            return False

        # Read consents in reverse (most recent first)
        with open(self.consent_file, 'r') as f:
            lines = f.readlines()

        for line in reversed(lines):
            if not line.strip():
                continue

            record_dict = json.loads(line)
            if (record_dict['user_id'] == user_id and
                record_dict['purpose'] == purpose.value):
                return record_dict['granted']

        return False

    def create_data_subject_request(
        self,
        user_id: str,
        right: DataSubjectRight
    ) -> DataSubjectRequest:
        """
        Create data subject request.

        Args:
            user_id: User identifier
            right: Right being exercised

        Returns:
            DataSubjectRequest
        """
        import secrets

        request = DataSubjectRequest(
            request_id=secrets.token_hex(16),
            user_id=user_id,
            right=right,
            timestamp=datetime.utcnow().isoformat() + 'Z',
            status='pending'
        )

        # Append to requests log
        with open(self.requests_file, 'a') as f:
            f.write(json.dumps(request.to_dict()) + '\n')

        return request

    def update_request_status(
        self,
        request_id: str,
        status: str,
        notes: str = ""
    ):
        """
        Update data subject request status.

        Args:
            request_id: Request identifier
            status: New status
            notes: Status notes
        """
        # This is simplified - production would use database
        # For now, append status update
        update = {
            'request_id': request_id,
            'status': status,
            'notes': notes,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

        status_file = self.compliance_dir / "request_updates.jsonl"
        with open(status_file, 'a') as f:
            f.write(json.dumps(update) + '\n')

    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Export all data for user (right to portability).

        Args:
            user_id: User identifier

        Returns:
            Dictionary with all user data
        """
        # Collect all user data
        export = {
            'user_id': user_id,
            'export_date': datetime.utcnow().isoformat() + 'Z',
            'consents': [],
            'requests': []
        }

        # Export consents
        if self.consent_file.exists():
            with open(self.consent_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    if record['user_id'] == user_id:
                        export['consents'].append(record)

        # Export requests
        if self.requests_file.exists():
            with open(self.requests_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    request = json.loads(line)
                    if request['user_id'] == user_id:
                        export['requests'].append(request)

        return export

    def delete_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Delete all data for user (right to erasure).

        Args:
            user_id: User identifier

        Returns:
            Report of deleted data
        """
        # This is simplified - production would use proper deletion
        # For now, record deletion request
        deletion_record = {
            'user_id': user_id,
            'deletion_date': datetime.utcnow().isoformat() + 'Z',
            'method': 'secure_delete',
            'categories_deleted': [
                DataCategory.PERSONAL_DATA.value,
                DataCategory.OPERATIONAL_DATA.value
            ]
        }

        deletion_file = self.compliance_dir / "deletions.jsonl"
        with open(deletion_file, 'a') as f:
            f.write(json.dumps(deletion_record) + '\n')

        return deletion_record

    def generate_compliance_report(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate compliance report for date range.

        Args:
            start_date: Report start date
            end_date: Report end date

        Returns:
            Compliance report
        """
        report = {
            'report_period': {
                'start': start_date.isoformat() + 'Z',
                'end': end_date.isoformat() + 'Z'
            },
            'generated': datetime.utcnow().isoformat() + 'Z',
            'consents': {
                'total': 0,
                'granted': 0,
                'denied': 0,
                'by_purpose': {}
            },
            'data_subject_requests': {
                'total': 0,
                'by_right': {},
                'by_status': {}
            },
            'retention_policies': [
                {
                    'category': p.category.value,
                    'retention_days': p.retention_days,
                    'legal_basis': p.legal_basis
                }
                for p in self._retention_policies.values()
            ]
        }

        # Count consents
        if self.consent_file.exists():
            with open(self.consent_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    record_date = datetime.fromisoformat(record['timestamp'].rstrip('Z'))

                    if start_date <= record_date <= end_date:
                        report['consents']['total'] += 1
                        if record['granted']:
                            report['consents']['granted'] += 1
                        else:
                            report['consents']['denied'] += 1

                        purpose = record['purpose']
                        report['consents']['by_purpose'][purpose] = \
                            report['consents']['by_purpose'].get(purpose, 0) + 1

        # Count data subject requests
        if self.requests_file.exists():
            with open(self.requests_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    request = json.loads(line)
                    request_date = datetime.fromisoformat(request['timestamp'].rstrip('Z'))

                    if start_date <= request_date <= end_date:
                        report['data_subject_requests']['total'] += 1

                        right = request['right']
                        report['data_subject_requests']['by_right'][right] = \
                            report['data_subject_requests']['by_right'].get(right, 0) + 1

                        status = request['status']
                        report['data_subject_requests']['by_status'][status] = \
                            report['data_subject_requests']['by_status'].get(status, 0) + 1

        return report


class DataMinimizer:
    """
    Enforces data minimization principles.

    Only collects and retains data necessary for stated purpose.
    """

    def __init__(self):
        self._required_fields: Dict[str, Set[str]] = {}

    def register_purpose(self, purpose: str, required_fields: Set[str]):
        """
        Register data requirements for purpose.

        Args:
            purpose: Processing purpose
            required_fields: Set of required field names
        """
        self._required_fields[purpose] = required_fields

    def minimize_data(self, purpose: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Minimize data to only required fields.

        Args:
            purpose: Processing purpose
            data: Full data dictionary

        Returns:
            Minimized data with only required fields
        """
        if purpose not in self._required_fields:
            logging.warning(f"No data requirements registered for purpose: {purpose}")
            return data

        required = self._required_fields[purpose]
        return {k: v for k, v in data.items() if k in required}

    def validate_collection(self, purpose: str, data: Dict[str, Any]) -> bool:
        """
        Validate that data collection is minimal.

        Returns:
            True if collection is minimal, False if excessive
        """
        if purpose not in self._required_fields:
            return True

        required = self._required_fields[purpose]
        collected = set(data.keys())

        # Check for excessive collection
        excessive = collected - required
        if excessive:
            logging.warning(f"Excessive data collection for {purpose}: {excessive}")
            return False

        return True
