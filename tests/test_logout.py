import pytest
from httpx import AsyncClient
from freezegun import freeze_time

from app.core.redis_client import redis_client
from app.api.auth import _create_access_token_raw, decode_token


class TestLogoutBasic:

    @pytest.mark.asyncio
    async def test_logout_returns_success_message(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'alice',
            'password': 'alicepass'
        })
        assert login_response.status_code == 200
        token = login_response.json()['access_token']

        logout_response = await client.post('/logout', data={'token': token})
        assert logout_response.status_code == 200
        assert logout_response.json()['msg'] == 'Successfully logged out'

    @pytest.mark.asyncio
    async def test_logout_requires_token(self, client: AsyncClient):
        response = await client.post('/logout', data={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_logout_empty_token_returns_error(self, client: AsyncClient):
        response = await client.post('/logout', data={'token': ''})
        assert response.status_code == 422


class TestTokenInvalidationAfterLogout:

    @pytest.mark.asyncio
    async def test_token_cannot_access_protected_endpoint_after_logout(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'alice',
            'password': 'alicepass'
        })
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        me_response = await client.get('/me', headers=headers)
        assert me_response.status_code == 200

        await client.post('/logout', data={'token': token})

        me_response_after = await client.get('/me', headers=headers)
        assert me_response_after.status_code == 401
        assert 'revoked' in me_response_after.text.lower()

    @pytest.mark.asyncio
    async def test_token_moved_to_blacklist_after_logout(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'alice',
            'password': 'alicepass'
        })
        token = login_response.json()['access_token']

        payload = decode_token(token)
        jti = payload.get('jti')

        assert redis_client.is_blacklisted(jti) is False

        await client.post('/logout', data={'token': token})

        assert redis_client.is_blacklisted(jti) is True

    @pytest.mark.asyncio
    async def test_removed_from_whitelist_after_logout(self, client: AsyncClient):
        'After logout, token should be removed from whitelist.'
        login_resp = await client.post('/login', json={
            'username': 'alice',
            'password': 'alicepass'
        })
        token = login_resp.json()['access_token']

        payload = decode_token(token)
        jti = payload.get('jti')

        assert redis_client.is_whitelisted(jti) is True

        await client.post('/logout', data={'token': token})

        assert redis_client.is_whitelisted(jti) is False


class TestLogoutEdgeCases:

    @pytest.mark.asyncio
    async def test_logout_invalid_token_format(self, client: AsyncClient):
        response = await client.post('/logout', data={'token': 'invalid.token'})
        assert response.status_code == 400
        assert 'Invalid token' in response.text

    @pytest.mark.asyncio
    async def test_logout_tampered_token(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'alice',
            'password': 'alicepass'
        })
        valid_token = login_response.json()['access_token']

        parts = valid_token.split('.')
        tampered = f'{parts[0]}.{parts[1]}.invalid_signature'

        response = await client.post('/logout', data={'token': tampered})
        assert response.status_code == 400
        assert 'Invalid token' in response.text

    @pytest.mark.asyncio
    async def test_logout_already_revoked_token(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'alice',
            'password': 'alicepass'
        })
        token = login_response.json()['access_token']

        first_response = await client.post('/logout', data={'token': token})
        assert first_response.status_code == 200

        second_response = await client.post('/logout', data={'token': token})
        assert second_response.status_code == 400
        assert 'already' in second_response.text.lower() or 'inactive' in second_response.text.lower()

    @pytest.mark.asyncio
    async def test_logout_token_without_jti(self, client: AsyncClient):
        from app.api.auth import create_access_token
        token_without_jti = _create_access_token_raw({'sub': 'alice', 'role': 'role1'})

        response = await client.post('/logout', data={'token': token_without_jti})
        assert response.status_code == 400
        assert 'Invalid token format' in response.text or 'jti' in response.text.lower()


class TestLogoutWithMultipleTokens:

    @pytest.mark.asyncio
    async def test_logout_one_token_does_not_affect_other_tokens(self, client: AsyncClient):
        first_login_response = await client.post('/login', json={
            'username': 'alice',
            'password': 'alicepass'
        })
        first_token = first_login_response.json()['access_token']

        second_login_response = await client.post('/login', json={
            'username': 'alice',
            'password': 'alicepass'
        })
        second_token = second_login_response.json()['access_token']

        first_headers = {'Authorization': f'Bearer {first_token}'}
        second_headers = {'Authorization': f'Bearer {second_token}'}

        first_response = await client.get('/me', headers=first_headers)
        second_response = await client.get('/me', headers=second_headers)
        assert first_response.status_code == 200
        assert second_response.status_code == 200

        await client.post('/logout', data={'token': first_token})

        first_response_after = await client.get('/me', headers=first_headers)
        assert first_response_after.status_code == 401

        second_response_after = await client.get('/me', headers=second_headers)
        assert second_response_after.status_code == 200

    @pytest.mark.asyncio
    async def test_logout_does_not_affect_other_users_tokens(self, client: AsyncClient):
        login_alice = await client.post('/login', json={
            'username': 'alice',
            'password': 'alicepass'
        })
        alice_token = login_alice.json()['access_token']

        login_bob = await client.post('/login', json={
            'username': 'bob',
            'password': 'bobpass'
        })
        bob_token = login_bob.json()['access_token']

        await client.post('/logout', data={'token': alice_token})

        bob_headers = {'Authorization': f'Bearer {bob_token}'}
        bob_me = await client.get('/me', headers=bob_headers)
        assert bob_me.status_code == 200
        assert bob_me.json()['username'] == 'bob'


class TestLogoutIdempotency:

    @pytest.mark.asyncio
    async def test_logout_idempotent_behavior(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'admin',
            'password': 'adminpass'
        })
        token = login_response.json()['access_token']

        first_response = await client.post('/logout', data={'token': token})
        assert first_response.status_code == 200

        second_response = await client.post('/logout', data={'token': token})
        assert second_response.status_code == 400


class TestLogoutAfterExpiration:

    @freeze_time('2026-01-01 12:00:00')
    @pytest.mark.asyncio
    async def test_logout_expired_token_returns_error(self, client: AsyncClient):
        from app.api.auth import create_access_token
        from datetime import timedelta

        with freeze_time('2026-01-01 12:00:00'):
            token = create_access_token(
                {'sub': 'alice', 'role': 'role1', 'jti': 'test.jti.token'},
                expires_delta=timedelta(minutes=1)
            )

        with freeze_time('2026-01-01 12:02:00'):
            response = await client.post('/logout', data={'token': token})
            assert response.status_code == 400
            assert 'Invalid token' in response.text


class TestLogoutRedisUnavailable:

    @pytest.mark.asyncio
    async def test_logout_handles_redis_unavailable_gracefully(self, client: AsyncClient, monkeypatch):
        from app.core import redis_client as redis_module

        class MockRedisClient:
            def is_whitelisted(self, jti):
                return False

            def is_blacklisted(self, jti):
                return False

            def add_to_blacklist(self, jti):
                return False

            def remove_from_whitelist(self, jti):
                return False

            def ping(self):
                return False

        monkeypatch.setattr(redis_module, 'redis_client', MockRedisClient())

        from app.api.auth import create_access_token
        token = create_access_token({'sub': 'alice', 'role': 'role1', 'jti': 'test-jti'})

        response = await client.post('/logout', data={'token': token})
        assert response.status_code in (400, 503)
