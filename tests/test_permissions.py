import pytest
from modules.permissions.rbac import (
    create_role,
    get_role,
    get_role_by_name,
    list_roles,
    create_permission,
    list_permissions,
    assign_role_to_user,
    remove_role_from_user,
    get_user_roles,
    get_user_permissions,
    user_has_permission,
    assign_permission_to_role,
)


class TestRoles:
    def test_create_role(self):
        role = create_role("test_role", "Test role description")
        assert role["name"] == "test_role"
        assert role["description"] == "Test role description"

        fetched = get_role(role["id"])
        assert fetched is not None
        assert fetched["name"] == "test_role"

    def test_get_role_by_name(self):
        create_role("unique_role", "Unique")
        role = get_role_by_name("unique_role")
        assert role is not None
        assert role["name"] == "unique_role"

    def test_list_roles(self):
        create_role("role_a", "")
        create_role("role_b", "")
        roles = list_roles()
        names = [r["name"] for r in roles]
        assert "role_a" in names
        assert "role_b" in names


class TestPermissions:
    def test_create_permission(self):
        perm = create_permission("test_resource", "test_action", "Test description")
        assert perm["resource"] == "test_resource"
        assert perm["action"] == "test_action"

    def test_list_permissions(self):
        create_permission("res_a", "act_a", "")
        create_permission("res_b", "act_b", "")
        perms = list_permissions()
        resources = [(p["resource"], p["action"]) for p in perms]
        assert ("res_a", "act_a") in resources
        assert ("res_b", "act_b") in resources


class TestRBAC:
    def test_assign_role_to_user(self, test_user):
        role = create_role("editor", "Can edit")
        assign_role_to_user(test_user, role["id"], granted_by="system")
        roles = get_user_roles(test_user)
        assert any(r["name"] == "editor" for r in roles)

    def test_remove_role_from_user(self, test_user):
        role = create_role("viewer", "Can view")
        assign_role_to_user(test_user, role["id"])
        remove_role_from_user(test_user, role["id"])
        roles = get_user_roles(test_user)
        assert not any(r["name"] == "viewer" for r in roles)

    def test_user_has_permission(self, test_user):
        role = create_role("writer", "Can write")
        perm = create_permission("docs", "write", "Write documents")
        assign_permission_to_role(role["id"], perm["id"])
        assign_role_to_user(test_user, role["id"])

        assert user_has_permission(test_user, "docs", "write")
        assert not user_has_permission(test_user, "docs", "delete")

    def test_user_permissions_list(self, test_user):
        role = create_role("manager", "Manages")
        p1 = create_permission("users", "read", "Read users")
        p2 = create_permission("users", "list", "List users")

        assign_permission_to_role(role["id"], p1["id"])
        assign_permission_to_role(role["id"], p2["id"])
        assign_role_to_user(test_user, role["id"])

        perms = get_user_permissions(test_user)
        actions = [(p["resource"], p["action"]) for p in perms]
        assert ("users", "read") in actions
        assert ("users", "list") in actions

    def test_multiple_roles_permissions(self, test_user):
        r1 = create_role("role1", "")
        r2 = create_role("role2", "")
        p1 = create_permission("res1", "action1", "")
        p2 = create_permission("res2", "action2", "")

        assign_permission_to_role(r1["id"], p1["id"])
        assign_permission_to_role(r2["id"], p2["id"])
        assign_role_to_user(test_user, r1["id"])
        assign_role_to_user(test_user, r2["id"])

        assert user_has_permission(test_user, "res1", "action1")
        assert user_has_permission(test_user, "res2", "action2")
