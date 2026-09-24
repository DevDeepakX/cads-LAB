class InvestigationService:
    def __init__(self, provider, finding_engine):
        self.provider = provider
        self.finding_engine = finding_engine

    def get_finding(self, session_id, finding_id):
        return self.finding_engine.get_finding(session_id, finding_id)

    def investigate(self, session_id, finding_id):
        finding = self.get_finding(session_id, finding_id)
        if not finding:
            return None
        self.finding_engine.update_status(session_id, finding_id, "INVESTIGATING")
        return self.get_details(session_id, finding_id)

    def get_details(self, session_id, finding_id):
        finding = self.get_finding(session_id, finding_id)
        if not finding:
            return None
        events = self.get_related_events(session_id, finding["resource_id"])
        return {"finding": finding, "resource": self.provider.get_resource(session_id, finding["resource_id"]), "events": events, "timeline": events}

    def get_related_events(self, session_id, resource_id=None):
        events = self.provider.list_events(session_id)
        if resource_id is not None:
            events = [event for event in events if event.get("resource_name") == resource_id or event.get("resource_id") == resource_id]
        return sorted(events, key=lambda event: event["timestamp"])

    def get_timeline(self, session_id):
        return self.get_related_events(session_id)