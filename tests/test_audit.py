import pytest
from modules.audit.logger import audit_log, get_audit_logs


class TestAuditLog:
    def test_create_audit_log(self, test_user):
        audit_log(
            username=test_user,
            action="test_action",
            resource="test_resource",
            details="Testing audit logging",
        )
        logs = get_audit_logs(username=test_user)
        assert len(logs) >= 1
        assert logs[0]["action"] == "test_action"
        assert logs[0]["status"] == "success"

    def test_audit_log_filter_by_action(self, test_user):
        audit_log(test_user, "action_a", resource="r1")
        audit_log(test_user, "action_b", resource="r2")

        logs_a = get_audit_logs(action="action_a")
        assert all("action_a" in l["action"] for l in logs_a)

    def test_audit_log_filter_by_status(self, test_user):
        audit_log(test_user, "ok_action", status="success")
        audit_log(test_user, "denied_action", status="denied")

        denied = get_audit_logs(status="denied")
        assert len(denied) >= 1
        assert all(l["status"] == "denied" for l in denied)

    def test_audit_log_pagination(self, test_user):
        for i in range(15):
            audit_log(test_user, f"bulk_action_{i}", resource="bulk")

        first_page = get_audit_logs(limit=10, offset=0)
        second_page = get_audit_logs(limit=10, offset=10)
        assert len(first_page) <= 10
        total = len(first_page) + len(second_page)
        assert total >= 15
