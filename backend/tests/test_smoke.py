"""
Smoke tests for every API endpoint.

These tests hit each URL and assert the response is not a 500.
The goal is to catch serializer bugs, broken queries, missing migrations,
and import errors *before* they reach production.

Run with:
    DJANGO_SETTINGS_MODULE=config.settings.test pytest tests/test_smoke.py -v
"""

import pytest
from django.test import override_settings

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Disable per-view cache_page decorators so we don't get stale cached
# responses from one test affecting another.
NO_CACHE = {"CACHE_TIMEOUTS": {}}


def assert_not_500(response, url: str):
    """Any status < 500 is fine (200, 201, 400, 401, 403, 404 are all OK).
    A 500 means something is broken in our code."""
    assert (
        response.status_code < 500
    ), f"{url} returned {response.status_code}: {response.content[:300]}"


# ===========================================================================
# Core / Health
# ===========================================================================


class TestHealthEndpoints:
    """Health and readiness probes."""

    def test_ready_check(self, api_client):
        resp = api_client.get("/api/ready/")
        assert resp.status_code == 200

    def test_health_check(self, api_client):
        """Health check tests DB and Redis. In test env Redis may not be
        available, so we only assert no 500 (503 for unhealthy is fine)."""
        resp = api_client.get("/api/health/")
        assert_not_500(resp, "/api/health/")


# ===========================================================================
# Congress API — Members
# ===========================================================================


@override_settings(**NO_CACHE)
class TestMemberEndpoints:
    """All /api/v1/members/ routes."""

    def test_list_empty(self, api_client, db):
        resp = api_client.get("/api/v1/members/")
        assert resp.status_code == 200

    def test_list_with_data(self, api_client, member, senator):
        resp = api_client.get("/api/v1/members/")
        assert resp.status_code == 200
        assert resp.json()["count"] == 2

    def test_retrieve(self, api_client, member):
        resp = api_client.get(f"/api/v1/members/{member.bioguide_id}/")
        assert resp.status_code == 200

    def test_retrieve_not_found(self, api_client, db):
        resp = api_client.get("/api/v1/members/DOESNOTEXIST/")
        assert resp.status_code == 404

    def test_representatives_action(self, api_client, member, senator):
        resp = api_client.get("/api/v1/members/representatives/")
        assert resp.status_code == 200

    def test_senators_action(self, api_client, member, senator):
        resp = api_client.get("/api/v1/members/senators/")
        assert resp.status_code == 200

    def test_zip_lookup_valid(self, api_client, db):
        """Zip lookup with a valid format but unknown zip — should 404, not 500."""
        resp = api_client.get("/api/v1/members/zip-lookup/?zip=00000")
        assert_not_500(resp, "/api/v1/members/zip-lookup/")

    def test_zip_lookup_invalid(self, api_client, db):
        resp = api_client.get("/api/v1/members/zip-lookup/?zip=abc")
        assert resp.status_code == 400

    def test_zip_lookup_missing(self, api_client, db):
        resp = api_client.get("/api/v1/members/zip-lookup/")
        assert resp.status_code == 400

    # -- Filters --

    def test_filter_by_party(self, api_client, member, senator):
        resp = api_client.get("/api/v1/members/?party=D")
        assert resp.status_code == 200

    def test_filter_by_chamber(self, api_client, member, senator):
        resp = api_client.get("/api/v1/members/?chamber=senate")
        assert resp.status_code == 200

    def test_filter_by_state(self, api_client, member):
        resp = api_client.get("/api/v1/members/?state=CA")
        assert resp.status_code == 200


# ===========================================================================
# Congress API — Bills
# ===========================================================================


@override_settings(**NO_CACHE)
class TestBillEndpoints:
    """All /api/v1/bills/ routes."""

    def test_list_empty(self, api_client, db):
        resp = api_client.get("/api/v1/bills/")
        assert resp.status_code == 200

    def test_list_with_data(self, api_client, bill):
        resp = api_client.get("/api/v1/bills/")
        assert resp.status_code == 200
        assert resp.json()["count"] >= 1

    def test_retrieve(self, api_client, bill):
        resp = api_client.get(f"/api/v1/bills/{bill.bill_id}/")
        assert resp.status_code == 200

    def test_retrieve_not_found(self, api_client, db):
        resp = api_client.get("/api/v1/bills/nonexistent-999/")
        assert resp.status_code == 404

    def test_calendar_action(self, api_client, bill):
        resp = api_client.get("/api/v1/bills/calendar/")
        assert resp.status_code == 200

    def test_calendar_with_dates(self, api_client, bill):
        resp = api_client.get(
            "/api/v1/bills/calendar/?date_from=2025-01-01&date_to=2025-12-31"
        )
        assert resp.status_code == 200


# ===========================================================================
# Congress API — Votes
# ===========================================================================


@override_settings(**NO_CACHE)
class TestVoteEndpoints:
    """All /api/v1/votes/ routes."""

    def test_list_empty(self, api_client, db):
        resp = api_client.get("/api/v1/votes/")
        assert resp.status_code == 200

    def test_list_with_data(self, api_client, vote):
        resp = api_client.get("/api/v1/votes/")
        assert resp.status_code == 200

    def test_retrieve(self, api_client, vote):
        resp = api_client.get(f"/api/v1/votes/{vote.vote_id}/")
        assert resp.status_code == 200

    def test_retrieve_not_found(self, api_client, db):
        resp = api_client.get("/api/v1/votes/nonexistent/")
        assert resp.status_code == 404

    def test_calendar_action(self, api_client, vote):
        resp = api_client.get("/api/v1/votes/calendar/")
        assert resp.status_code == 200

    def test_calendar_with_dates(self, api_client, vote):
        resp = api_client.get(
            "/api/v1/votes/calendar/?date_from=2025-01-01&date_to=2025-12-31"
        )
        assert resp.status_code == 200


# ===========================================================================
# Congress API — Seats (Hemicycle)
# ===========================================================================


@override_settings(**NO_CACHE)
class TestSeatEndpoints:
    """All /api/v1/seats/ routes."""

    def test_list_empty(self, api_client, db):
        resp = api_client.get("/api/v1/seats/")
        assert resp.status_code == 200

    def test_list_with_chamber_filter(self, api_client, seat):
        resp = api_client.get("/api/v1/seats/?chamber=house")
        assert resp.status_code == 200

    def test_vote_overlay_missing_params(self, api_client, db):
        resp = api_client.get("/api/v1/seats/vote-overlay/")
        assert resp.status_code == 400

    def test_vote_overlay_missing_vote_id(self, api_client, db):
        resp = api_client.get("/api/v1/seats/vote-overlay/?chamber=house")
        assert resp.status_code == 400

    def test_vote_overlay_with_data(self, api_client, seat, vote, member_vote):
        resp = api_client.get(
            f"/api/v1/seats/vote-overlay/?chamber=house&vote_id={vote.vote_id}"
        )
        assert resp.status_code == 200


# ===========================================================================
# Content API — Weekly Summaries
# ===========================================================================


@override_settings(**NO_CACHE)
class TestWeeklySummaryEndpoints:
    """All /api/v1/content/weekly-summaries/ routes."""

    def test_list_empty(self, api_client, db):
        resp = api_client.get("/api/v1/content/weekly-summaries/")
        assert resp.status_code == 200

    def test_list_with_data(self, api_client, weekly_summary):
        resp = api_client.get("/api/v1/content/weekly-summaries/")
        assert resp.status_code == 200

    def test_retrieve(self, api_client, weekly_summary):
        resp = api_client.get(f"/api/v1/content/weekly-summaries/{weekly_summary.pk}/")
        assert resp.status_code == 200

    def test_retrieve_not_found(self, api_client, db):
        resp = api_client.get("/api/v1/content/weekly-summaries/99999/")
        assert resp.status_code == 404

    def test_current_action(self, api_client, weekly_summary):
        resp = api_client.get("/api/v1/content/weekly-summaries/current/")
        assert resp.status_code == 200

    def test_week_action(self, api_client, weekly_summary):
        resp = api_client.get("/api/v1/content/weekly-summaries/week/2025/1/")
        assert resp.status_code == 200

    def test_week_action_not_found(self, api_client, db):
        resp = api_client.get("/api/v1/content/weekly-summaries/week/2020/1/")
        assert resp.status_code == 404

    def test_week_action_invalid(self, api_client, db):
        resp = api_client.get("/api/v1/content/weekly-summaries/week/2025/99/")
        assert resp.status_code == 400


# ===========================================================================
# Auth API — Public endpoints
# ===========================================================================


class TestAuthPublicEndpoints:
    """Auth endpoints that should be accessible without authentication."""

    def test_me_unauthenticated(self, api_client, db):
        """GET /me without auth should return 401, not 500."""
        resp = api_client.get("/api/v1/auth/me/")
        assert resp.status_code == 401

    def test_token_refresh_no_body(self, api_client, db):
        """POST with no refresh token should return 400, not 500."""
        resp = api_client.post("/api/v1/auth/token/refresh/", {})
        assert_not_500(resp, "/api/v1/auth/token/refresh/")

    def test_social_sync_no_secret(self, api_client, db):
        """POST without the sync secret should return 403, not 500."""
        resp = api_client.post(
            "/api/v1/auth/social-sync/",
            {"email": "a@b.com", "provider": "google"},
            format="json",
        )
        assert resp.status_code == 403


# ===========================================================================
# Auth API — Authenticated endpoints
# ===========================================================================


class TestAuthProtectedEndpoints:
    """Auth endpoints that require authentication."""

    def test_me_get(self, auth_client):
        resp = auth_client.get("/api/v1/auth/me/")
        assert resp.status_code == 200

    def test_api_keys_list(self, auth_client):
        resp = auth_client.get("/api/v1/auth/api-keys/")
        assert resp.status_code == 200

    def test_api_keys_create_invalid(self, auth_client):
        """Missing fields → 400, not 500."""
        resp = auth_client.post("/api/v1/auth/api-keys/create/", {}, format="json")
        assert_not_500(resp, "/api/v1/auth/api-keys/create/")

    def test_api_keys_delete_not_found(self, auth_client):
        resp = auth_client.delete("/api/v1/auth/api-keys/nonexistent/delete/")
        assert resp.status_code == 404

    def test_my_representatives(self, auth_client):
        resp = auth_client.get("/api/v1/auth/my-representatives/")
        assert resp.status_code == 200

    def test_my_representatives_activity(self, auth_client):
        resp = auth_client.get("/api/v1/auth/my-representatives/activity/")
        assert resp.status_code == 200

    def test_follow_member_not_found(self, auth_client):
        resp = auth_client.post("/api/v1/auth/follow/DOESNOTEXIST/")
        assert resp.status_code == 404

    def test_follow_member(self, auth_client, member):
        resp = auth_client.post(f"/api/v1/auth/follow/{member.bioguide_id}/")
        assert resp.status_code in (200, 201)

    def test_unfollow_member_not_following(self, auth_client, member):
        resp = auth_client.delete(f"/api/v1/auth/follow/{member.bioguide_id}/")
        assert resp.status_code == 404

    def test_follow_then_unfollow(self, auth_client, member):
        auth_client.post(f"/api/v1/auth/follow/{member.bioguide_id}/")
        resp = auth_client.delete(f"/api/v1/auth/follow/{member.bioguide_id}/")
        assert resp.status_code == 204

    def test_chat_stream_no_body(self, auth_client):
        """POST chat/stream with no body → 400-level, not 500."""
        resp = auth_client.post("/api/v1/auth/chat/stream/", {}, format="json")
        assert_not_500(resp, "/api/v1/auth/chat/stream/")

    def test_chat_stream_invalid_provider(self, auth_client):
        resp = auth_client.post(
            "/api/v1/auth/chat/stream/",
            {"provider": "invalid", "messages": [{"role": "user", "content": "hi"}]},
            format="json",
        )
        assert_not_500(resp, "/api/v1/auth/chat/stream/")


# ===========================================================================
# Auth API — Unauthenticated access to protected endpoints
# ===========================================================================


class TestAuthEndpointsRequireAuth:
    """Verify protected endpoints return 401 instead of 500 for anon users."""

    @pytest.mark.parametrize(
        "method,url",
        [
            ("get", "/api/v1/auth/me/"),
            ("get", "/api/v1/auth/api-keys/"),
            ("post", "/api/v1/auth/api-keys/create/"),
            ("delete", "/api/v1/auth/api-keys/test/delete/"),
            ("get", "/api/v1/auth/my-representatives/"),
            ("get", "/api/v1/auth/my-representatives/activity/"),
            ("post", "/api/v1/auth/follow/T000001/"),
            ("delete", "/api/v1/auth/follow/T000001/"),
            ("post", "/api/v1/auth/chat/stream/"),
        ],
    )
    def test_returns_401(self, api_client, db, method, url):
        resp = getattr(api_client, method)(url)
        assert resp.status_code == 401, f"{method.upper()} {url} should require auth"


# ===========================================================================
# DRF Router — Auto-discovered endpoints
# ===========================================================================


@override_settings(**NO_CACHE)
class TestRouterAPIRoot:
    """The DRF DefaultRouter creates an API root view listing all endpoints."""

    def test_api_root(self, api_client, db):
        resp = api_client.get("/api/v1/")
        assert resp.status_code == 200

    def test_content_api_root(self, api_client, db):
        resp = api_client.get("/api/v1/content/")
        assert resp.status_code == 200
