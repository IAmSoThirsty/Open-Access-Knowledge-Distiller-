"""
Production Monitoring and Metrics Module

Provides operational observability for production deployments:
- Real-time performance metrics
- Health checks and liveness probes
- Error tracking and alerting
- Resource usage monitoring
- SLA compliance tracking
"""

import time
import psutil
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque
import threading


class HealthStatus(Enum):
    """System health status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: HealthStatus
    message: str
    timestamp: str
    duration_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'timestamp': self.timestamp,
            'duration_ms': self.duration_ms,
            'metadata': self.metadata
        }


@dataclass
class Metric:
    """Metric data point"""
    name: str
    metric_type: MetricType
    value: float
    timestamp: str
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'type': self.metric_type.value,
            'value': self.value,
            'timestamp': self.timestamp,
            'labels': self.labels
        }


class MetricsCollector:
    """
    Collects and aggregates system metrics.

    Tracks:
    - Processing throughput
    - Latency percentiles
    - Error rates
    - Resource utilization
    """

    def __init__(self, window_size: int = 1000):
        """
        Initialize metrics collector.

        Args:
            window_size: Number of recent samples to retain for statistics
        """
        self.window_size = window_size
        self._counters: Dict[str, float] = {}
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, deque] = {}
        self._timers: Dict[str, deque] = {}
        self._lock = threading.Lock()

    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] = self._counters.get(key, 0.0) + value

    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Set a gauge metric"""
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value

    def record_value(self, name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a histogram value"""
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._histograms:
                self._histograms[key] = deque(maxlen=self.window_size)
            self._histograms[key].append(value)

    def record_timing(self, name: str, duration_ms: float, labels: Optional[Dict[str, str]] = None):
        """Record a timing measurement"""
        with self._lock:
            key = self._make_key(name, labels)
            if key not in self._timers:
                self._timers[key] = deque(maxlen=self.window_size)
            self._timers[key].append(duration_ms)

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get counter value"""
        key = self._make_key(name, labels)
        return self._counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        """Get gauge value"""
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0.0)

    def get_percentiles(
        self,
        name: str,
        percentiles: List[float] = [50, 95, 99],
        labels: Optional[Dict[str, str]] = None
    ) -> Dict[float, float]:
        """Get percentile values for histogram"""
        key = self._make_key(name, labels)
        if key not in self._histograms or not self._histograms[key]:
            return {p: 0.0 for p in percentiles}

        values = sorted(self._histograms[key])
        result = {}
        for p in percentiles:
            idx = int(len(values) * p / 100)
            result[p] = values[min(idx, len(values) - 1)]
        return result

    def get_all_metrics(self) -> List[Metric]:
        """Get all current metrics"""
        metrics = []
        timestamp = datetime.utcnow().isoformat() + 'Z'

        with self._lock:
            # Counters
            for key, value in self._counters.items():
                name, labels = self._parse_key(key)
                metrics.append(Metric(
                    name=name,
                    metric_type=MetricType.COUNTER,
                    value=value,
                    timestamp=timestamp,
                    labels=labels
                ))

            # Gauges
            for key, value in self._gauges.items():
                name, labels = self._parse_key(key)
                metrics.append(Metric(
                    name=name,
                    metric_type=MetricType.GAUGE,
                    value=value,
                    timestamp=timestamp,
                    labels=labels
                ))

        return metrics

    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create metric key from name and labels"""
        if not labels:
            return name
        label_str = ','.join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _parse_key(self, key: str) -> tuple:
        """Parse metric key into name and labels"""
        if '{' not in key:
            return key, {}

        name, label_part = key.split('{', 1)
        label_part = label_part.rstrip('}')

        labels = {}
        if label_part:
            for pair in label_part.split(','):
                k, v = pair.split('=')
                labels[k] = v

        return name, labels

    def reset(self):
        """Reset all metrics"""
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._timers.clear()


class HealthMonitor:
    """
    Monitors system health and provides health check endpoints.

    Checks:
    - Resource availability
    - Component responsiveness
    - Dependency health
    """

    def __init__(self):
        self._health_checks: Dict[str, Callable[[], tuple]] = {}
        self._last_check_results: Dict[str, HealthCheck] = {}

    def register_check(self, name: str, check_func: Callable[[], tuple]):
        """
        Register a health check.

        Args:
            name: Check name
            check_func: Function returning (status: HealthStatus, message: str, metadata: dict)
        """
        self._health_checks[name] = check_func

    def check_health(self) -> Dict[str, Any]:
        """
        Run all health checks.

        Returns:
            Overall health status and individual check results
        """
        results = []
        worst_status = HealthStatus.HEALTHY

        for name, check_func in self._health_checks.items():
            start = time.time()
            try:
                status, message, metadata = check_func()
                duration_ms = (time.time() - start) * 1000
            except Exception as e:
                status = HealthStatus.CRITICAL
                message = f"Health check failed: {str(e)}"
                metadata = {'error': str(e)}
                duration_ms = (time.time() - start) * 1000

            check_result = HealthCheck(
                name=name,
                status=status,
                message=message,
                timestamp=datetime.utcnow().isoformat() + 'Z',
                duration_ms=duration_ms,
                metadata=metadata
            )

            results.append(check_result)
            self._last_check_results[name] = check_result

            # Track worst status
            if status.value == 'critical':
                worst_status = HealthStatus.CRITICAL
            elif status.value == 'unhealthy' and worst_status != HealthStatus.CRITICAL:
                worst_status = HealthStatus.UNHEALTHY
            elif status.value == 'degraded' and worst_status == HealthStatus.HEALTHY:
                worst_status = HealthStatus.DEGRADED

        return {
            'status': worst_status.value,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'checks': [r.to_dict() for r in results]
        }

    def get_check(self, name: str) -> Optional[HealthCheck]:
        """Get last result for specific check"""
        return self._last_check_results.get(name)


class ResourceMonitor:
    """
    Monitors system resource usage.

    Tracks:
    - CPU usage
    - Memory usage
    - Disk I/O
    - Network I/O
    """

    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        # Get process-specific stats
        process = psutil.Process()
        process_memory = process.memory_info()

        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'system': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_mb': memory.used / (1024 * 1024),
                'memory_total_mb': memory.total / (1024 * 1024),
                'disk_percent': disk.percent,
                'disk_used_gb': disk.used / (1024 ** 3),
                'disk_total_gb': disk.total / (1024 ** 3)
            },
            'process': {
                'memory_rss_mb': process_memory.rss / (1024 * 1024),
                'memory_vms_mb': process_memory.vms / (1024 * 1024),
                'cpu_percent': process.cpu_percent(interval=0.1),
                'num_threads': process.num_threads()
            }
        }

    def check_resource_limits(
        self,
        max_cpu_percent: float = 90.0,
        max_memory_percent: float = 90.0,
        max_disk_percent: float = 90.0
    ) -> tuple:
        """
        Check if resources are within limits.

        Returns:
            (status: HealthStatus, message: str, metadata: dict)
        """
        usage = self.get_resource_usage()
        system = usage['system']

        issues = []

        if system['cpu_percent'] > max_cpu_percent:
            issues.append(f"CPU usage {system['cpu_percent']:.1f}% exceeds {max_cpu_percent}%")

        if system['memory_percent'] > max_memory_percent:
            issues.append(f"Memory usage {system['memory_percent']:.1f}% exceeds {max_memory_percent}%")

        if system['disk_percent'] > max_disk_percent:
            issues.append(f"Disk usage {system['disk_percent']:.1f}% exceeds {max_disk_percent}%")

        if not issues:
            return HealthStatus.HEALTHY, "Resource usage within limits", usage
        elif len(issues) == 1:
            return HealthStatus.DEGRADED, issues[0], usage
        else:
            return HealthStatus.UNHEALTHY, "; ".join(issues), usage


class SLATracker:
    """
    Tracks SLA compliance metrics.

    Monitors:
    - Availability
    - Latency targets
    - Error rates
    - Throughput
    """

    def __init__(
        self,
        target_availability: float = 99.9,
        target_p95_latency_ms: float = 1000.0,
        target_error_rate: float = 0.01
    ):
        """
        Initialize SLA tracker.

        Args:
            target_availability: Target uptime percentage
            target_p95_latency_ms: Target 95th percentile latency in ms
            target_error_rate: Target error rate (0.01 = 1%)
        """
        self.target_availability = target_availability
        self.target_p95_latency_ms = target_p95_latency_ms
        self.target_error_rate = target_error_rate

        self.total_requests = 0
        self.failed_requests = 0
        self.latencies = deque(maxlen=10000)
        self.uptime_start = datetime.utcnow()
        self.downtime_seconds = 0.0

    def record_request(self, success: bool, latency_ms: float):
        """Record a request"""
        self.total_requests += 1
        if not success:
            self.failed_requests += 1
        self.latencies.append(latency_ms)

    def record_downtime(self, duration_seconds: float):
        """Record downtime period"""
        self.downtime_seconds += duration_seconds

    def get_sla_compliance(self) -> Dict[str, Any]:
        """Get current SLA compliance status"""
        # Calculate availability
        total_seconds = (datetime.utcnow() - self.uptime_start).total_seconds()
        uptime_seconds = total_seconds - self.downtime_seconds
        availability = (uptime_seconds / total_seconds * 100) if total_seconds > 0 else 100.0

        # Calculate error rate
        error_rate = (self.failed_requests / self.total_requests) if self.total_requests > 0 else 0.0

        # Calculate P95 latency
        if self.latencies:
            sorted_latencies = sorted(self.latencies)
            p95_idx = int(len(sorted_latencies) * 0.95)
            p95_latency = sorted_latencies[min(p95_idx, len(sorted_latencies) - 1)]
        else:
            p95_latency = 0.0

        return {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'availability': {
                'current': availability,
                'target': self.target_availability,
                'compliant': availability >= self.target_availability
            },
            'latency_p95_ms': {
                'current': p95_latency,
                'target': self.target_p95_latency_ms,
                'compliant': p95_latency <= self.target_p95_latency_ms
            },
            'error_rate': {
                'current': error_rate,
                'target': self.target_error_rate,
                'compliant': error_rate <= self.target_error_rate
            },
            'total_requests': self.total_requests,
            'failed_requests': self.failed_requests,
            'uptime_hours': uptime_seconds / 3600
        }


class AlertManager:
    """
    Manages alerts and notifications.

    Features:
    - Alert deduplication
    - Alert severity levels
    - Notification callbacks
    """

    def __init__(self):
        self._alert_handlers: List[Callable] = []
        self._active_alerts: Dict[str, datetime] = {}
        self._alert_cooldown = timedelta(minutes=5)

    def register_handler(self, handler: Callable[[str, str, Dict], None]):
        """
        Register alert handler.

        Args:
            handler: Function(severity, message, metadata) -> None
        """
        self._alert_handlers.append(handler)

    def send_alert(self, severity: str, message: str, metadata: Optional[Dict] = None):
        """
        Send alert if not in cooldown.

        Args:
            severity: Alert severity (info, warning, error, critical)
            message: Alert message
            metadata: Additional alert metadata
        """
        metadata = metadata or {}
        alert_key = f"{severity}:{message}"

        # Check cooldown
        now = datetime.utcnow()
        if alert_key in self._active_alerts:
            if now - self._active_alerts[alert_key] < self._alert_cooldown:
                return  # Skip duplicate alert in cooldown

        # Update active alerts
        self._active_alerts[alert_key] = now

        # Call handlers
        for handler in self._alert_handlers:
            try:
                handler(severity, message, metadata)
            except Exception as e:
                logging.error(f"Alert handler failed: {e}")

    def clear_alert(self, severity: str, message: str):
        """Clear active alert"""
        alert_key = f"{severity}:{message}"
        self._active_alerts.pop(alert_key, None)


class CircuitBreaker:
    """
    Circuit breaker for fault isolation.

    Prevents cascading failures by failing fast when error threshold exceeded.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open

    def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection.

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == 'open':
            if self._should_attempt_reset():
                self.state = 'half_open'
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return (time.time() - self.last_failure_time) >= self.recovery_timeout

    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        self.state = 'closed'

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = 'open'

    def reset(self):
        """Manually reset circuit breaker"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'
