from datetime import datetime


def generate_event(session_id, service, event_name, actor="student", resource_type="UNKNOWN", resource_name="", source_ip="10.0.0.15", region="ap-south-1", outcome="SUCCESS", severity="MEDIUM", metadata=None):
    from .cloud_simulator import create_cloud_event

    metadata = metadata or {}
    metadata.setdefault("resource_name", resource_name)
    return create_cloud_event(
        session_id=session_id,
        service=service,
        event_name=event_name,
        actor=actor,
        resource_type=resource_type,
        source_ip=source_ip,
        region=region,
        outcome=outcome,
        severity=severity,
        metadata=metadata,
    )
