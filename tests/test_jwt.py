from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt
from freezegun import freeze_time

from app.api.auth import _create_access_token_raw, decode_token
from app.core.config import settings


class TestJWTTokenCreation:

    def test_create_access_token_returns_string(self):
        token = _create_access_token_raw({'sub': 'testuser'})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_has_three_parts(self):
        token = _create_access_token_raw({'sub': 'testuser'})
        parts = token.split('.')
        assert len(parts) == 3

    def test_create_access_token_contains_subject(self):
        token = _create_access_token_raw({'sub': 'testuser', 'role': 'admin'})
        payload = decode_token(token)
        assert payload['sub'] == 'testuser'
        assert payload['role'] == 'admin'

    def test_create_access_token_with_custom_expire(self):
        custom_expiry = timedelta(minutes=5)
        token = _create_access_token_raw(
            {'sub': 'testuser'},
            expires_delta=custom_expiry
        )
        payload = decode_token(token)
        exp_timestamp = payload['exp']
        expected_exp = datetime.now(timezone.utc) + custom_expiry

        # Allow 1 second tolerance
        assert abs(exp_timestamp - expected_exp.timestamp()) < 1

    def test_create_access_token_uses_config_expire_by_default(self):
        settings.access_token_expire_minutes = 60
        token = _create_access_token_raw({'sub': 'testuser'})
        payload = decode_token(token)
        exp_timestamp = payload['exp']
        expected_exp = datetime.now(timezone.utc) + timedelta(minutes=60)

        # Allow 1 second tolerance
        assert abs(exp_timestamp - expected_exp.timestamp()) < 1


class TestJWTTokenDecoding:

    def test_decode_valid_token(self):
        original_payload = {'sub': 'testuser', 'user_id': 123}
        token = _create_access_token_raw(original_payload)
        decoded = decode_token(token)

        assert decoded is not None
        assert decoded['sub'] == 'testuser'
        assert decoded['user_id'] == 123

    def test_decode_token_returns_none_for_invalid_token(self):
        invalid_token = 'not.a.valid.token'
        assert decode_token(invalid_token) is None

    def test_decode_token_returns_none_for_tampered_token(self):
        token = _create_access_token_raw({'sub': 'testuser'})

        parts = token.split('.')
        tampered = f'{parts[0]}.tampered.{parts[2]}'
        assert decode_token(tampered) is None

    def test_decode_token_returns_none_for_empty_string(self):
        assert decode_token('') is None

    def test_decode_token_for_wrong_algorithm(self):
        wrong_token = jwt.encode(
            {'sub': 'testuser'},
            settings.secret_key,
            algorithm='HS384' # Different from settings.algorithm
        )
        assert decode_token(wrong_token) is None


class TestJWTExpiration:

    @freeze_time('2026-01-01 12:00:00')
    def test_token_is_valid_before_expiry(self):
        settings.access_token_expire_minutes = 30
        token = _create_access_token_raw({'sub': 'testuser'})
        assert decode_token(token) is not None

    @freeze_time('2026-01-01 12:00:00')
    def test_token_expires_after_configured_time(self):
        settings.access_token_expire_minutes = 30
        token = _create_access_token_raw({'sub': 'testuser'})

        with freeze_time('2026-01-01 12:31:00'):
            assert decode_token(token) is None

    @freeze_time('2026-01-01 12:00:00')
    def test_custom_expiry_overrides_default(self):
        settings.access_token_expire_minutes = 60
        token = _create_access_token_raw(
            {'sub': 'testuser'},
            expires_delta=timedelta(minutes=5)
        )

        with freeze_time('2026-01-01 12:10:00'):
            assert decode_token(token) is None

    @freeze_time('2026-01-01 12:00:00')
    def test_token_has_exp_claim(self):
        token = _create_access_token_raw({'sub': 'testuser'})
        payload = decode_token(token)
        assert 'exp' in payload
        assert isinstance(payload['exp'], (int, float))


class TestJWTSecurity:

    def test_invalid_token_signature(self):
        token = _create_access_token_raw({'sub': 'alice'})

        parts = token.split('.')
        modified = f'{parts[0]}.{parts[1]}.invalid_signature'

        assert decode_token(modified) is None

    def test_no_algorithm(self):
        import json
        import base64

        header = base64.urlsafe_b64encode(
            json.dumps({'alg': 'none', 'type': 'JWT'}).encode()
        ).decode().rstrip('=')
        payload = base64.urlsafe_b64encode(
            json.dumps({'sub': 'attacker', 'role': 'admin'}).encode()
        ).decode().rstrip('=')
        malicious_token = f'{header}.{payload}'

        assert decode_token(malicious_token) is None

    def test_token_contains_jti(self):
        from unittest.mock import patch
        import uuid

        mock_uuid = '123y1232-t23d-23e3-s798-374829472999'
        with patch('uuid.uuid4', return_value=mock_uuid):
            token = _create_access_token_raw({'sub': 'testuser', 'jti': mock_uuid})
            payload = decode_token(token)
            assert payload.get('jti') == mock_uuid
