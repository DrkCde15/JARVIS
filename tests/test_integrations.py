import os
import pytest


class TestGitHubClient:
    def test_init_without_token(self):
        from integrations.github.client import GitHubClient

        client = GitHubClient(token=None)
        assert client._api_base == "https://api.github.com"

    def test_init_with_token(self):
        from integrations.github.client import GitHubClient

        client = GitHubClient(token="test_token_123")
        assert client.token == "test_token_123"

    def test_headers(self):
        from integrations.github.client import GitHubClient

        client = GitHubClient(token="mytoken")
        headers = client._headers()
        assert headers["Authorization"] == "Bearer mytoken"
        assert "User-Agent" in headers

    def test_health_check_fail(self):
        from integrations.github.client import GitHubClient

        client = GitHubClient(token="invalid_token")
        assert not client.check_health()


class TestGitLabClient:
    def test_init_without_token(self):
        from integrations.gitlab.client import GitLabClient

        client = GitLabClient(token=None)
        assert client.url == "https://gitlab.com"

    def test_init_custom_url(self):
        from integrations.gitlab.client import GitLabClient

        client = GitLabClient(token="token", url="https://gitlab.example.com")
        assert client.url == "https://gitlab.example.com"
        assert client._api_base == "https://gitlab.example.com/api/v4"

    def test_headers(self):
        from integrations.gitlab.client import GitLabClient

        client = GitLabClient(token="glpat-test")
        headers = client._headers()
        assert headers["PRIVATE-TOKEN"] == "glpat-test"

    def test_health_check_fail(self):
        from integrations.gitlab.client import GitLabClient

        client = GitLabClient(token="bad_token")
        assert not client.check_health()
