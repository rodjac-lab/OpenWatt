# Structured Logging Guide

## Overview

OpenWatt uses **structlog** for structured JSON logging, enabling:
- ✅ Machine-readable logs (ELK, CloudWatch, Datadog, etc.)
- ✅ Request correlation via `request_id`
- ✅ Rich context (user_id, tariff_id, supplier, etc.)
- ✅ Production observability

---

## Quick Start

### Basic Usage

```python
from api.app.core.logging import get_logger

logger = get_logger(__name__)

# Simple log
logger.info("user_logged_in", user_id=123)

# With context
logger.info(
    "tariff_created",
    tariff_id=456,
    supplier="EDF",
    option="BASE",
    puissance_kva=6
)

# Error with exception
try:
    result = risky_operation()
except Exception as exc:
    logger.error("operation_failed", exc_info=exc, operation="risky_operation")
```

### Output Example

```json
{
  "event": "tariff_created",
  "tariff_id": 456,
  "supplier": "EDF",
  "option": "BASE",
  "puissance_kva": 6,
  "level": "info",
  "timestamp": "2025-11-15T20:30:45.123Z",
  "logger": "api.app.services.tariff_service",
  "service": "OpenWatt API",
  "environment": "production",
  "request_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "method": "POST",
  "path": "/v1/tariffs",
  "client_ip": "192.168.1.100"
}
```

---

## Request Correlation

Every HTTP request gets a unique `request_id` automatically via `RequestIDMiddleware`.

### Flow

1. **Client sends request** (optional `X-Request-ID` header)
2. **Middleware generates UUID4** if not provided
3. **Binds to structlog context** for all logs in this request
4. **Returns in response header** `X-Request-ID`

### Example

```bash
# Client request
curl -H "X-Request-ID: custom-123" http://localhost:8000/v1/tariffs

# All logs for this request will have:
{
  "request_id": "custom-123",
  ...
}

# Response includes header
X-Request-ID: custom-123
```

### Accessing Request ID in Code

```python
from fastapi import Request

async def my_endpoint(request: Request):
    request_id = request.state.request_id
    logger.info("processing_request", custom_field=request_id)
```

---

## Log Levels

Use appropriate log levels:

| Level | Usage | Example |
|-------|-------|---------|
| `DEBUG` | Development details | `logger.debug("query_executed", sql="SELECT ...")` |
| `INFO` | Normal operations | `logger.info("tariff_fetched", tariff_id=123)` |
| `WARNING` | Recoverable issues | `logger.warning("rate_limit_approached", current=90, max=100)` |
| `ERROR` | Application errors | `logger.error("db_connection_failed", exc_info=exc)` |
| `CRITICAL` | System failures | `logger.critical("database_unreachable")` |

---

## Best Practices

### ✅ DO

```python
# Use structured fields
logger.info("user_action", user_id=123, action="login", ip="1.2.3.4")

# Use snake_case for event names
logger.info("tariff_comparison_completed")

# Include relevant context
logger.info("pdf_parsed", supplier="EDF", rows_extracted=42, parser_version="v2")

# Log exceptions with exc_info
try:
    parse_pdf(file)
except Exception as exc:
    logger.error("pdf_parsing_failed", filename=file.name, exc_info=exc)
```

### ❌ DON'T

```python
# Don't use string formatting
logger.info(f"User {user_id} logged in")  # ❌ Not structured

# Don't log sensitive data
logger.info("password_validated", password=secret)  # ❌ Security risk

# Don't log in tight loops without sampling
for item in million_items:
    logger.info("processing_item", item_id=item.id)  # ❌ Log spam
```

---

## Configuration

### Environment Variables

Set log level via environment:

```bash
export OPENWATT_LOG_LEVEL=DEBUG  # For development
export OPENWATT_LOG_LEVEL=INFO   # For production (default)
```

### Custom Processors

Add custom processors in `api/app/core/logging.py`:

```python
def add_custom_field(logger: Any, method_name: str, event_dict: EventDict) -> EventDict:
    event_dict["deployment"] = "eu-west-1"
    return event_dict

# Add to processors list in configure_logging()
processors.append(add_custom_field)
```

---

## Integration with Monitoring

### ELK Stack (Elasticsearch, Logstash, Kibana)

JSON logs are directly ingestible:

```bash
# Pipe logs to Logstash
uvicorn api.app.main:app | logstash -f logstash.conf
```

**Logstash config**:
```ruby
input {
  stdin { codec => json }
}
filter {
  # Logs are already JSON, no parsing needed
}
output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "openwatt-%{+YYYY.MM.dd}"
  }
}
```

### CloudWatch Logs

AWS CloudWatch Logs Insights queries:

```sql
# Find all errors for a specific request
fields @timestamp, event, level, request_id
| filter request_id = "f47ac10b-58cc-4372-a567-0e02b2c3d479"
| sort @timestamp desc

# Tariff creation errors
fields @timestamp, event, supplier, exc_info
| filter event = "tariff_created" and level = "error"
| limit 100
```

### Datadog

Enable JSON parsing in Datadog agent:

```yaml
logs:
  - type: file
    path: /var/log/openwatt/*.log
    service: openwatt-api
    source: python
    sourcecategory: sourcecode
    log_processing_rules:
      - type: json_parser
        name: parse_json
```

---

## Filtering Logs

### Development (human-readable)

For local development, use console renderer:

```python
# In api/app/core/logging.py
processors.append(structlog.dev.ConsoleRenderer())  # Instead of JSONRenderer
```

Output:
```
2025-11-15 20:30:45 [info     ] tariff_created      tariff_id=456 supplier=EDF
```

### Production (JSON)

Use `JSONRenderer` (default) for structured logs.

---

## Examples

### Service Layer

```python
# api/app/services/tariff_service.py
from api.app.core.logging import get_logger

logger = get_logger(__name__)

async def create_tariff(data: TariffCreate) -> Tariff:
    logger.info("tariff_creation_started", supplier=data.supplier)

    try:
        tariff = await repository.create(data)
        logger.info(
            "tariff_created",
            tariff_id=tariff.id,
            supplier=tariff.supplier,
            option=tariff.option
        )
        return tariff
    except Exception as exc:
        logger.error(
            "tariff_creation_failed",
            supplier=data.supplier,
            exc_info=exc
        )
        raise
```

### Ingestion Pipeline

```python
# ingest/pipeline.py
from api.app.core.logging import get_logger

logger = get_logger(__name__)

def run_ingestion(supplier: str):
    logger.info("ingestion_started", supplier=supplier)

    try:
        records = fetch_tariffs(supplier)
        logger.info("tariffs_fetched", supplier=supplier, count=len(records))

        inserted = persist_to_db(records)
        logger.info(
            "ingestion_completed",
            supplier=supplier,
            records_inserted=inserted,
            duration_seconds=duration
        )
    except Exception as exc:
        logger.error("ingestion_failed", supplier=supplier, exc_info=exc)
        # Optionally send alert (Slack, Sentry)
        raise
```

---

## Troubleshooting

### No logs appearing

Check log level:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### Logs not JSON formatted

Ensure `JSONRenderer` is last processor:
```python
processors.append(structlog.processors.JSONRenderer())
```

### Request ID not in logs

Verify middleware is added:
```python
# In api/app/main.py
app.add_middleware(RequestIDMiddleware)
```

---

## Migration from Standard Logging

### Before (stdlib logging)

```python
import logging

logging.info(f"User {user_id} logged in from {ip}")
```

### After (structlog)

```python
from api.app.core.logging import get_logger

logger = get_logger(__name__)
logger.info("user_logged_in", user_id=user_id, ip=ip)
```

---

## Performance

Structlog is highly optimized:
- **Lazy binding**: Context only serialized when logged
- **Caching**: Loggers cached on first use
- **Minimal overhead**: ~2-5µs per log entry

For high-throughput endpoints, use sampling:

```python
import random

if random.random() < 0.01:  # Log 1% of requests
    logger.debug("request_sampled", endpoint="/v1/tariffs")
```

---

## References

- [Structlog Documentation](https://www.structlog.org/)
- [12-Factor App Logs](https://12factor.net/logs)
- [OpenWatt Spec-Kit](../specs/constitution.md)
