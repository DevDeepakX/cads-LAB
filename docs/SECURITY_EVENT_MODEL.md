# Security Event Model

All simulator events use one structure:

```json
{
  "event_id": "evt-session-001-0001",
  "session_id": "session-001",
  "timestamp": "2026-09-24T20:00:00+00:00",
  "service": "S3",
  "event_name": "GetBucketPolicy",
  "actor": "student",
  "resource_id": "cads-public-data",
  "resource_name": "cads-public-data",
  "resource_type": "S3_BUCKET",
  "source_ip": "10.10.10.10",
  "region": "ap-south-1",
  "outcome": "SUCCESS",
  "severity": "MEDIUM",
  "metadata": {}
}
```

`SimulatorProvider.create_event` appends the event and immediately sends it to `EventProcessor`. Events are retained per lab session and are returned chronologically by the investigation service. Resource configuration can include a classification such as `PUBLIC`, `INTERNAL`, `CONFIDENTIAL`, or `SENSITIVE`.

The same pipeline handles discovery, simulated object access, and defensive actions. No event path executes shell input or accesses a real filesystem.