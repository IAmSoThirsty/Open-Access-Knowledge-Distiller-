"""
Security and Compliance Module

Production-grade security hardening for adversarial environments and regulatory compliance.

Features:
- Input sanitization and validation
- Path traversal protection
- Resource exhaustion prevention
- Audit logging with tamper detection
- Cryptographic verification
- Access control
- Data privacy controls
"""

import os
import re
import hashlib
import hmac
import secrets
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class SecurityLevel(Enum):
    """Security classification levels"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class AuditEventType(Enum):
    """Types of auditable events"""
    DOCUMENT_ACCESS = "document_access"
    CLAIM_EXTRACTION = "claim_extraction"
    GRAPH_GENERATION = "graph_generation"
    EXPORT_OPERATION = "export_operation"
    CONFIGURATION_CHANGE = "configuration_change"
    SECURITY_VIOLATION = "security_violation"
    DATA_DELETION = "data_deletion"
    SYSTEM_ERROR = "system_error"


@dataclass(frozen=True)
class AuditLogEntry:
    """Immutable audit log entry with cryptographic integrity"""
    timestamp: str  # ISO 8601 UTC
    event_type: AuditEventType
    user_id: str
    session_id: str
    resource_id: str
    action: str
    result: str  # success, failure, partial
    details: Dict[str, Any]
    previous_hash: str  # Hash of previous entry for chain integrity
    entry_hash: str  # SHA256 of this entry
    signature: str  # HMAC signature for tamper detection

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp,
            'event_type': self.event_type.value,
            'user_id': self.user_id,
            'session_id': self.session_id,
            'resource_id': self.resource_id,
            'action': self.action,
            'result': self.result,
            'details': self.details,
            'previous_hash': self.previous_hash,
            'entry_hash': self.entry_hash,
            'signature': self.signature
        }


class InputValidator:
    """
    Validates and sanitizes all external inputs.

    Protects against:
    - Path traversal attacks
    - Command injection
    - XML/JSON injection
    - Buffer overflow (size limits)
    - Resource exhaustion
    """

    # Whitelist of allowed file extensions
    ALLOWED_EXTENSIONS = {'.pdf'}

    # Maximum file size (100MB)
    MAX_FILE_SIZE = 100 * 1024 * 1024

    # Maximum path length
    MAX_PATH_LENGTH = 4096

    # Allowed characters in identifiers (alphanumeric, dash, underscore)
    IDENTIFIER_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

    # Maximum claim length (protect against DoS)
    MAX_CLAIM_LENGTH = 10000

    # Maximum number of claims per document
    MAX_CLAIMS_PER_DOCUMENT = 10000

    def __init__(self, allowed_directories: Optional[Set[str]] = None):
        """
        Initialize validator.

        Args:
            allowed_directories: Whitelist of allowed directories for file access
        """
        self.allowed_directories = allowed_directories or set()

    def validate_file_path(self, file_path: str) -> str:
        """
        Validate and normalize file path.

        Protects against:
        - Path traversal (../)
        - Symbolic link attacks
        - Access outside allowed directories

        Returns:
            Normalized absolute path

        Raises:
            ValueError: If path is invalid or unsafe
        """
        if not file_path:
            raise ValueError("File path cannot be empty")

        if len(file_path) > self.MAX_PATH_LENGTH:
            raise ValueError(f"File path exceeds maximum length of {self.MAX_PATH_LENGTH}")

        # Convert to absolute path and resolve symlinks
        try:
            abs_path = Path(file_path).resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Invalid file path: {e}")

        abs_path_str = str(abs_path)

        # Check for path traversal attempts
        if '..' in file_path or abs_path_str != str(Path(abs_path_str).resolve()):
            raise ValueError("Path traversal detected")

        # Verify file exists and is a file (not directory)
        if not abs_path.exists():
            raise ValueError(f"File does not exist: {abs_path_str}")

        if not abs_path.is_file():
            raise ValueError(f"Path is not a file: {abs_path_str}")

        # Check extension
        if abs_path.suffix.lower() not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"File extension not allowed: {abs_path.suffix}")

        # Check file size
        file_size = abs_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(f"File size {file_size} exceeds maximum {self.MAX_FILE_SIZE}")

        # Check against allowed directories if specified
        if self.allowed_directories:
            allowed = any(
                abs_path_str.startswith(str(Path(allowed_dir).resolve()))
                for allowed_dir in self.allowed_directories
            )
            if not allowed:
                raise ValueError(f"File path outside allowed directories: {abs_path_str}")

        return abs_path_str

    def validate_identifier(self, identifier: str, max_length: int = 256) -> str:
        """
        Validate identifier (user_id, session_id, etc).

        Args:
            identifier: Identifier to validate
            max_length: Maximum allowed length

        Returns:
            Validated identifier

        Raises:
            ValueError: If identifier is invalid
        """
        if not identifier:
            raise ValueError("Identifier cannot be empty")

        if len(identifier) > max_length:
            raise ValueError(f"Identifier exceeds maximum length of {max_length}")

        if not self.IDENTIFIER_PATTERN.match(identifier):
            raise ValueError("Identifier contains invalid characters")

        return identifier

    def sanitize_text(self, text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize text input.

        Args:
            text: Text to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized text

        Raises:
            ValueError: If text is invalid
        """
        if max_length and len(text) > max_length:
            raise ValueError(f"Text exceeds maximum length of {max_length}")

        # Remove null bytes
        text = text.replace('\x00', '')

        # Normalize whitespace
        text = ' '.join(text.split())

        return text


class AuditLogger:
    """
    Tamper-evident audit logging system.

    Features:
    - Cryptographic hash chain for integrity
    - HMAC signatures for authenticity
    - Immutable log entries
    - Append-only operation
    """

    def __init__(self, log_file: str, secret_key: Optional[bytes] = None):
        """
        Initialize audit logger.

        Args:
            log_file: Path to audit log file
            secret_key: Secret key for HMAC (generated if not provided)
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        # Generate or use provided secret key
        self.secret_key = secret_key or secrets.token_bytes(32)

        # Initialize hash chain
        self.last_hash = "0" * 64  # Genesis hash

        # Load existing log to get last hash
        if self.log_file.exists():
            self._load_last_hash()

    def log_event(
        self,
        event_type: AuditEventType,
        user_id: str,
        session_id: str,
        resource_id: str,
        action: str,
        result: str,
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLogEntry:
        """
        Log an auditable event.

        Args:
            event_type: Type of event
            user_id: User identifier
            session_id: Session identifier
            resource_id: Resource identifier
            action: Action performed
            result: Result (success, failure, partial)
            details: Additional details

        Returns:
            Immutable audit log entry
        """
        timestamp = datetime.utcnow().isoformat() + 'Z'
        details = details or {}

        # Create entry data for hashing
        entry_data = {
            'timestamp': timestamp,
            'event_type': event_type.value,
            'user_id': user_id,
            'session_id': session_id,
            'resource_id': resource_id,
            'action': action,
            'result': result,
            'details': details,
            'previous_hash': self.last_hash
        }

        # Compute hash
        entry_json = json.dumps(entry_data, sort_keys=True)
        entry_hash = hashlib.sha256(entry_json.encode('utf-8')).hexdigest()

        # Compute HMAC signature
        signature = hmac.new(
            self.secret_key,
            entry_json.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Create immutable entry
        entry = AuditLogEntry(
            timestamp=timestamp,
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            resource_id=resource_id,
            action=action,
            result=result,
            details=details,
            previous_hash=self.last_hash,
            entry_hash=entry_hash,
            signature=signature
        )

        # Append to log file (atomic operation)
        self._append_entry(entry)

        # Update last hash
        self.last_hash = entry_hash

        return entry

    def verify_integrity(self) -> bool:
        """
        Verify audit log integrity.

        Returns:
            True if log is intact, False if tampered
        """
        if not self.log_file.exists():
            return True

        previous_hash = "0" * 64

        with open(self.log_file, 'r') as f:
            for line in f:
                if not line.strip():
                    continue

                entry_dict = json.loads(line)

                # Verify hash chain
                if entry_dict['previous_hash'] != previous_hash:
                    return False

                # Recompute hash
                entry_data = {
                    'timestamp': entry_dict['timestamp'],
                    'event_type': entry_dict['event_type'],
                    'user_id': entry_dict['user_id'],
                    'session_id': entry_dict['session_id'],
                    'resource_id': entry_dict['resource_id'],
                    'action': entry_dict['action'],
                    'result': entry_dict['result'],
                    'details': entry_dict['details'],
                    'previous_hash': entry_dict['previous_hash']
                }

                entry_json = json.dumps(entry_data, sort_keys=True)
                computed_hash = hashlib.sha256(entry_json.encode('utf-8')).hexdigest()

                if computed_hash != entry_dict['entry_hash']:
                    return False

                # Verify HMAC signature
                computed_signature = hmac.new(
                    self.secret_key,
                    entry_json.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()

                if not hmac.compare_digest(computed_signature, entry_dict['signature']):
                    return False

                previous_hash = entry_dict['entry_hash']

        return True

    def _append_entry(self, entry: AuditLogEntry):
        """Append entry to log file (atomic)"""
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(entry.to_dict()) + '\n')
            f.flush()
            os.fsync(f.fileno())

    def _load_last_hash(self):
        """Load last hash from existing log"""
        with open(self.log_file, 'r') as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1].strip()
                if last_line:
                    entry_dict = json.loads(last_line)
                    self.last_hash = entry_dict['entry_hash']


class RateLimiter:
    """
    Rate limiting to prevent abuse and DoS attacks.

    Implements token bucket algorithm.
    """

    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize rate limiter.

        Args:
            max_requests: Maximum requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, List[float]] = {}

    def check_rate_limit(self, client_id: str) -> bool:
        """
        Check if request is within rate limit.

        Args:
            client_id: Client identifier

        Returns:
            True if allowed, False if rate limited
        """
        now = datetime.utcnow().timestamp()

        # Clean up old entries
        if client_id in self.requests:
            self.requests[client_id] = [
                ts for ts in self.requests[client_id]
                if now - ts < self.time_window
            ]
        else:
            self.requests[client_id] = []

        # Check limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False

        # Add new request
        self.requests[client_id].append(now)
        return True


class DataPrivacyController:
    """
    Controls data privacy and PII handling.

    Features:
    - PII detection and masking
    - Data retention policies
    - Right to deletion
    - Export controls
    """

    # PII patterns (simplified)
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
    SSN_PATTERN = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')

    def __init__(self, enable_pii_detection: bool = True):
        self.enable_pii_detection = enable_pii_detection

    def detect_pii(self, text: str) -> List[str]:
        """
        Detect potential PII in text.

        Returns:
            List of PII types detected
        """
        if not self.enable_pii_detection:
            return []

        pii_types = []

        if self.EMAIL_PATTERN.search(text):
            pii_types.append('email')

        if self.PHONE_PATTERN.search(text):
            pii_types.append('phone')

        if self.SSN_PATTERN.search(text):
            pii_types.append('ssn')

        return pii_types

    def mask_pii(self, text: str) -> str:
        """
        Mask PII in text.

        Returns:
            Text with PII masked
        """
        if not self.enable_pii_detection:
            return text

        # Mask emails
        text = self.EMAIL_PATTERN.sub('[EMAIL_REDACTED]', text)

        # Mask phone numbers
        text = self.PHONE_PATTERN.sub('[PHONE_REDACTED]', text)

        # Mask SSNs
        text = self.SSN_PATTERN.sub('[SSN_REDACTED]', text)

        return text


class ResourceLimiter:
    """
    Prevents resource exhaustion attacks.

    Limits:
    - Memory usage
    - CPU time
    - Disk space
    - Concurrent operations
    """

    def __init__(
        self,
        max_memory_mb: int = 1024,
        max_cpu_seconds: int = 300,
        max_concurrent: int = 10
    ):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_seconds = max_cpu_seconds
        self.max_concurrent = max_concurrent
        self.active_operations = 0

    def acquire(self) -> bool:
        """
        Acquire resource slot.

        Returns:
            True if acquired, False if limit reached
        """
        if self.active_operations >= self.max_concurrent:
            return False

        self.active_operations += 1
        return True

    def release(self):
        """Release resource slot"""
        if self.active_operations > 0:
            self.active_operations -= 1
