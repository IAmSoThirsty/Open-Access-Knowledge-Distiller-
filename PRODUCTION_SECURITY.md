# Production-Grade Security and Operations

OAKD is production-hardened for adversarial environments and regulatory compliance.

## Table of Contents

1. [Security Hardening](#security-hardening)
2. [Operational Monitoring](#operational-monitoring)
3. [Compliance Controls](#compliance-controls)
4. [Production Deployment](#production-deployment)
5. [Incident Response](#incident-response)

---

## Security Hardening

### Threat Model

OAKD defends against:
- **Path traversal attacks** (`../etc/passwd`)
- **Command injection** via filenames
- **Resource exhaustion** (DoS attacks)
- **Rate limit abuse**
- **Data exfiltration**
- **Audit log tampering**

### Input Validation

```python
from oakd import InputValidator

validator = InputValidator(allowed_directories={'/var/oakd/documents'})

# Validates file path, extension, size, and permissions
safe_path = validator.validate_file_path('/var/oakd/documents/paper.pdf')

# Validates identifiers (user_id, session_id)
user_id = validator.validate_identifier('user_12345')

# Sanitizes text (removes null bytes, normalizes whitespace)
clean_text = validator.sanitize_text(untrusted_input, max_length=10000)
```

**Protection:**
- Whitelisted file extensions (`.pdf` only)
- Maximum file size: 100MB
- Path traversal detection
- Symbolic link resolution
- Directory whitelist enforcement

### Audit Logging

Tamper-evident logging with cryptographic integrity:

```python
from oakd import AuditLogger, AuditEventType

logger = AuditLogger(
    log_file='.oakd_audit/audit.log',
    secret_key=b'your-32-byte-secret'  # Generate with secrets.token_bytes(32)
)

# Log events with hash chain
entry = logger.log_event(
    event_type=AuditEventType.DOCUMENT_ACCESS,
    user_id='user_12345',
    session_id='session_abc',
    resource_id='/docs/paper.pdf',
    action='process_document',
    result='success',
    details={'processing_time_ms': 1234}
)

# Verify integrity
if not logger.verify_integrity():
    raise SecurityException("Audit log has been tampered with!")
```

**Features:**
- SHA256 hash chain (each entry hashes the previous)
- HMAC signatures for authenticity
- Immutable log entries
- Atomic append-only operations
- Tamper detection

### Rate Limiting

Token bucket algorithm to prevent abuse:

```python
from oakd import RateLimiter

limiter = RateLimiter(max_requests=100, time_window=60)

if not limiter.check_rate_limit(client_id):
    raise Exception("Rate limit exceeded")
```

### Resource Protection

Prevents resource exhaustion attacks:

```python
from oakd import ResourceLimiter

limiter = ResourceLimiter(
    max_memory_mb=4096,
    max_cpu_seconds=3600,
    max_concurrent=10
)

# Acquire resource slot
if not limiter.acquire():
    raise Exception("System at capacity")

try:
    # Process document
    pass
finally:
    limiter.release()
```

### PII Detection

Automatic detection and masking of personal information:

```python
from oakd import DataPrivacyController

privacy = DataPrivacyController(enable_pii_detection=True)

# Detect PII types
pii_types = privacy.detect_pii("Contact: john.doe@example.com")
# Returns: ['email']

# Mask PII
masked = privacy.mask_pii("Contact: john.doe@example.com, 555-123-4567")
# Returns: "Contact: [EMAIL_REDACTED], [PHONE_REDACTED]"
```

---

## Operational Monitoring

### Metrics Collection

```python
from oakd import MetricsCollector

metrics = MetricsCollector(window_size=10000)

# Counter metrics
metrics.increment_counter('documents_processed', value=1)
metrics.increment_counter('claims_extracted', value=42)

# Gauge metrics (point-in-time values)
metrics.set_gauge('queue_depth', value=15)
metrics.set_gauge('active_sessions', value=3)

# Histogram values
metrics.record_value('claim_confidence', value=0.87)

# Timing measurements
metrics.record_timing('document_parsing_ms', duration_ms=1234.5)

# Get percentiles
p95 = metrics.get_percentiles('document_parsing_ms', percentiles=[50, 95, 99])
print(f"P95 latency: {p95[95]} ms")
```

### Health Checks

```python
from oakd import HealthMonitor, HealthStatus

monitor = HealthMonitor()

# Register custom health check
def check_database():
    try:
        # Check DB connection
        return HealthStatus.HEALTHY, "Database connected", {}
    except Exception as e:
        return HealthStatus.UNHEALTHY, f"Database error: {e}", {}

monitor.register_check("database", check_database)

# Run all checks
health = monitor.check_health()
print(f"Overall status: {health['status']}")
for check in health['checks']:
    print(f"  {check['name']}: {check['status']}")
```

### Resource Monitoring

```python
from oakd import ResourceMonitor

monitor = ResourceMonitor()

# Get current resource usage
usage = monitor.get_resource_usage()
print(f"CPU: {usage['system']['cpu_percent']}%")
print(f"Memory: {usage['system']['memory_percent']}%")
print(f"Disk: {usage['system']['disk_percent']}%")

# Check against limits
status, message, details = monitor.check_resource_limits(
    max_cpu_percent=90.0,
    max_memory_percent=90.0,
    max_disk_percent=95.0
)
```

### SLA Tracking

```python
from oakd import SLATracker

tracker = SLATracker(
    target_availability=99.9,
    target_p95_latency_ms=5000.0,
    target_error_rate=0.01
)

# Record requests
tracker.record_request(success=True, latency_ms=1234.5)
tracker.record_request(success=False, latency_ms=567.8)

# Record downtime
tracker.record_downtime(duration_seconds=30.0)

# Get compliance report
compliance = tracker.get_sla_compliance()
print(f"Availability: {compliance['availability']['current']:.2f}% "
      f"(target: {compliance['availability']['target']}%)")
print(f"P95 Latency: {compliance['latency_p95_ms']['current']:.1f} ms "
      f"(target: {compliance['latency_p95_ms']['target']} ms)")
```

### Alerting

```python
from oakd import AlertManager

alerts = AlertManager()

# Register alert handler
def send_email(severity, message, metadata):
    # Send email notification
    print(f"ALERT [{severity}]: {message}")

alerts.register_handler(send_email)

# Send alerts (with automatic deduplication)
alerts.send_alert(
    severity='critical',
    message='Audit log tampered',
    metadata={'file': '/var/log/audit.log'}
)
```

### Circuit Breaker

Fail-fast pattern to prevent cascading failures:

```python
from oakd import CircuitBreaker

breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0
)

# Protected function call
try:
    result = breaker.call(risky_operation, arg1, arg2)
except Exception as e:
    if breaker.state == 'open':
        print("Circuit is OPEN - failing fast")
    raise
```

---

## Compliance Controls

### Data Retention

```python
from oakd import ComplianceController, DataCategory

compliance = ComplianceController(compliance_dir='.oakd_compliance')

# Default policies:
# - Research data: 7 years
# - Operational data: 1 year
# - Audit data: 7 years
# - Personal data: 1 year or until consent withdrawn

# Get retention policy
policy = compliance.get_retention_policy(DataCategory.RESEARCH_DATA)
print(f"Retention: {policy.retention_days} days")
print(f"Legal basis: {policy.legal_basis}")
```

### Consent Management

```python
from oakd import ProcessingPurpose

# Record consent
consent = compliance.record_consent(
    user_id='user_12345',
    purpose=ProcessingPurpose.RESEARCH,
    granted=True,
    consent_text="I agree to allow my research documents to be processed...",
    ip_address='192.168.1.1',
    user_agent='Mozilla/5.0...'
)

# Check consent before processing
if not compliance.check_consent('user_12345', ProcessingPurpose.RESEARCH):
    raise Exception("User has not granted consent")
```

### Data Subject Rights

```python
from oakd import DataSubjectRight

# Right to access
export = compliance.export_user_data('user_12345')
# Returns all data for user in portable format

# Right to erasure (right to be forgotten)
deletion_report = compliance.delete_user_data('user_12345')

# Create data subject request
request = compliance.create_data_subject_request(
    user_id='user_12345',
    right=DataSubjectRight.ERASURE
)

# Update request status
compliance.update_request_status(
    request_id=request.request_id,
    status='completed',
    notes='All user data deleted'
)
```

### Compliance Reporting

```python
from datetime import datetime, timedelta

# Generate monthly compliance report
report = compliance.generate_compliance_report(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 1, 31)
)

print(f"Consents: {report['consents']['total']}")
print(f"  Granted: {report['consents']['granted']}")
print(f"  Denied: {report['consents']['denied']}")
print(f"Data Subject Requests: {report['data_subject_requests']['total']}")
```

### Data Minimization

```python
from oakd import DataMinimizer

minimizer = DataMinimizer()

# Register data requirements for purpose
minimizer.register_purpose(
    purpose='research',
    required_fields={'title', 'claims', 'citations'}
)

# Minimize data collection
full_data = {
    'title': 'Paper Title',
    'claims': [...],
    'citations': [...],
    'user_email': 'user@example.com',  # Not required for research
    'ip_address': '192.168.1.1'  # Not required for research
}

minimal_data = minimizer.minimize_data('research', full_data)
# Returns only: {'title', 'claims', 'citations'}
```

---

## Production Deployment

### Production Pipeline

```python
from oakd import EpistemicPipeline

# Full production configuration
pipeline = EpistemicPipeline(
    config_path='config/production.yaml',

    # Checkpointing
    checkpoint_dir='/var/oakd/checkpoints',
    enable_checkpoints=True,

    # Security
    audit_log_path='/var/log/oakd/audit.log',
    enable_security=True,
    allowed_directories={'/var/oakd/documents'},

    # Monitoring
    enable_monitoring=True,

    # Compliance
    compliance_dir='/var/oakd/compliance',
    enable_compliance=True,

    # Session tracking
    session_id='prod_session_123',
    user_id='system'
)

# Process with all protections
results = pipeline.process_deterministic(
    pdf_path='/var/oakd/documents/paper.pdf',
    output_path='/var/oakd/output/paper.json'
)

# Check health
health = pipeline.health_monitor.check_health()
if health['status'] != 'healthy':
    print("WARNING: System is degraded")

# Get metrics
metrics = pipeline.metrics.get_all_metrics()
for metric in metrics:
    print(f"{metric.name}: {metric.value}")

# Verify audit log
if not pipeline.audit_logger.verify_integrity():
    raise SecurityException("CRITICAL: Audit log tampered!")
```

### Docker Deployment

```dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 oakd && \
    mkdir -p /var/oakd/documents /var/oakd/checkpoints /var/oakd/compliance /var/log/oakd && \
    chown -R oakd:oakd /var/oakd /var/log/oakd

# Install OAKD
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY --chown=oakd:oakd . /app
WORKDIR /app

USER oakd

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "from oakd import EpistemicPipeline; p = EpistemicPipeline(); h = p.health_monitor.check_health(); exit(0 if h['status'] in ['healthy', 'degraded'] else 1)"

CMD ["python", "-m", "oakd.server"]
```

### Kubernetes Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: oakd-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: oakd
  template:
    metadata:
      labels:
        app: oakd
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: oakd
        image: oakd:1.0.0
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        env:
        - name: OAKD_AUDIT_LOG
          value: "/var/log/oakd/audit.log"
        - name: OAKD_COMPLIANCE_DIR
          value: "/var/oakd/compliance"
        volumeMounts:
        - name: documents
          mountPath: /var/oakd/documents
          readOnly: true
        - name: audit-logs
          mountPath: /var/log/oakd
        - name: compliance-data
          mountPath: /var/oakd/compliance
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
      volumes:
      - name: documents
        persistentVolumeClaim:
          claimName: oakd-documents
      - name: audit-logs
        persistentVolumeClaim:
          claimName: oakd-audit-logs
      - name: compliance-data
        persistentVolumeClaim:
          claimName: oakd-compliance
```

---

## Incident Response

### Security Incidents

#### Audit Log Tampering Detected

```python
# Verify audit log integrity
if not pipeline.audit_logger.verify_integrity():
    # CRITICAL: Audit log has been tampered with

    # 1. Isolate system
    pipeline.circuit_breaker.state = 'open'

    # 2. Alert security team
    pipeline.alert_manager.send_alert(
        severity='critical',
        message='Audit log integrity violation detected',
        metadata={
            'log_file': pipeline.audit_logger.log_file,
            'timestamp': datetime.utcnow().isoformat()
        }
    )

    # 3. Preserve evidence
    import shutil
    shutil.copy(
        pipeline.audit_logger.log_file,
        f'/var/oakd/forensics/audit_log_{datetime.utcnow().isoformat()}.evidence'
    )

    # 4. Initiate incident response
    raise SecurityIncident("Audit log tampered - system halted")
```

#### Rate Limit Abuse

```python
# Monitor for abuse patterns
if pipeline.rate_limiter.check_rate_limit(client_id):
    # Process request
    pass
else:
    # Log security violation
    pipeline.audit_logger.log_event(
        event_type=AuditEventType.SECURITY_VIOLATION,
        user_id=client_id,
        session_id=session_id,
        resource_id='rate_limiter',
        action='rate_limit_check',
        result='blocked',
        details={'reason': 'rate_limit_exceeded'}
    )

    # Check for persistent abuse
    # If client exceeds rate limit 10 times in 5 minutes, ban temporarily
    # (Implementation would track violations in database)
```

### Performance Degradation

```python
# Monitor SLA compliance
compliance = pipeline.sla_tracker.get_sla_compliance()

if not compliance['latency_p95_ms']['compliant']:
    # P95 latency exceeds target

    # 1. Alert operations team
    pipeline.alert_manager.send_alert(
        severity='warning',
        message=f"P95 latency {compliance['latency_p95_ms']['current']:.1f}ms exceeds target {compliance['latency_p95_ms']['target']}ms",
        metadata=compliance
    )

    # 2. Check resource usage
    usage = pipeline.resource_monitor.get_resource_usage()
    if usage['system']['cpu_percent'] > 90:
        # Scale horizontally (in Kubernetes)
        print("Trigger horizontal pod autoscaling")

    # 3. Enable rate limiting to protect system
    pipeline.rate_limiter.max_requests = 50  # Reduce to 50% capacity
```

### Compliance Violations

```python
# Check for missing consent
if not pipeline.compliance_controller.check_consent(user_id, ProcessingPurpose.RESEARCH):
    # User has not granted consent

    # 1. Stop processing
    raise ComplianceViolation(f"User {user_id} has not granted consent for research processing")

    # 2. Log compliance violation
    pipeline.audit_logger.log_event(
        event_type=AuditEventType.SECURITY_VIOLATION,
        user_id=user_id,
        session_id=session_id,
        resource_id=pdf_path,
        action='consent_check',
        result='violation',
        details={'reason': 'missing_consent', 'purpose': 'research'}
    )

    # 3. Notify DPO (Data Protection Officer)
    # (Send email/alert to compliance team)
```

---

## Best Practices

### 1. Secret Management

```python
import secrets

# Generate cryptographic keys
audit_secret = secrets.token_bytes(32)

# Store in secure key management system (Vault, AWS Secrets Manager, etc.)
# NEVER commit secrets to version control
```

### 2. Least Privilege

```python
# Restrict file access to specific directories
pipeline = EpistemicPipeline(
    allowed_directories={
        '/var/oakd/documents',  # Read-only document storage
        '/var/oakd/output'      # Write output here
    }
)
```

### 3. Defense in Depth

- Input validation at boundaries
- Rate limiting per client
- Resource limits per operation
- Audit logging for all actions
- Circuit breakers for fault isolation
- Regular integrity checks

### 4. Monitoring and Alerting

```python
# Set up monitoring
pipeline.health_monitor.register_check("custom_check", my_check_function)

# Configure alerts
pipeline.alert_manager.register_handler(send_to_pagerduty)
pipeline.alert_manager.register_handler(send_to_slack)

# Track SLAs
pipeline.sla_tracker.record_request(success=True, latency_ms=1234)
```

### 5. Regular Audits

```python
# Verify audit log integrity (run daily)
if not pipeline.audit_logger.verify_integrity():
    raise SecurityIncident("Audit log tampered")

# Generate compliance reports (run monthly)
report = pipeline.compliance_controller.generate_compliance_report(
    start_date=first_day_of_month,
    end_date=last_day_of_month
)

# Review data subject requests (run weekly)
# Ensure all requests completed within regulatory timeframes (30 days for GDPR)
```

---

## Security Contact

For security issues, contact: security@your-domain.com

PGP Key: [Your PGP public key]

**DO NOT** open public issues for security vulnerabilities.
