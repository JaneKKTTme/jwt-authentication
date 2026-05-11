import pytest
from httpx import AsyncClient


class TestCommonContent:

    @pytest.mark.asyncio
    async def test_role1_can_access_common_content(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'alice',
            'password': 'alicepass'
        })
        assert login_response.status_code == 200
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = await client.get('/content/common', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert 'content' in data
        assert 'common' in data['content'].lower()

    @pytest.mark.asyncio
    async def test_role2_can_access_common_content(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'bob',
            'password': 'bobpass'
        })
        assert login_response.status_code == 200
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = await client.get('/content/common', headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_can_access_common_content(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'admin',
            'password': 'adminpass'
        })
        assert login_response.status_code == 200
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = await client.get('/content/common', headers=headers)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unauthenticated_user_cannot_access_common_content(self, client: AsyncClient):
        response = await client.get('/content/common')
        assert response.status_code == 401
        assert 'not authenticated' in response.text.lower()


class TestRole1ExclusiveContent:

    @pytest.mark.asyncio
    async def test_role1_can_access_role1_content(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'alice',
            'password': 'alicepass'
        })
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = await client.get('/content/role1', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert 'role1' in data['content'].lower() or 'role 1' in data['content'].lower()

    @pytest.mark.asyncio
    async def test_role2_cannot_access_role1_content(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'bob',
            'password': 'bobpass'
        })
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = await client.get('/content/role1', headers=headers)
        assert response.status_code == 403
        assert 'missing permissions' in response.text.lower()

    @pytest.mark.asyncio
    async def test_admin_cannot_access_role1_content(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'admin',
            'password': 'adminpass'
        })
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = await client.get('/content/role1', headers=headers)
        assert response.status_code == 403
        assert 'missing permissions' in response.text.lower()

    @pytest.mark.asyncio
    async def test_unauthenticated_user_cannot_access_role1_content(self, client: AsyncClient):
        response = await client.get('/content/role1')
        assert response.status_code == 401


class TestRole2ExclusiveContent:

    @pytest.mark.asyncio
    async def test_role2_can_access_role2_content(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'bob',
            'password': 'bobpass'
        })
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = await client.get('/content/role2', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert 'role2' in data['content'].lower() or 'role 2' in data['content'].lower()

    @pytest.mark.asyncio
    async def test_role1_cannot_access_role2_content(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'alice',
            'password': 'alicepass'
        })
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = await client.get('/content/role2', headers=headers)
        assert response.status_code == 403
        assert 'missing permissions' in response.text.lower()

    @pytest.mark.asyncio
    async def test_admin_cannot_access_role2_content(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'admin',
            'password': 'adminpass'
        })
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = await client.get('/content/role2', headers=headers)
        assert response.status_code == 403
        assert 'missing permissions' in response.text.lower()

    @pytest.mark.asyncio
    async def test_unauthenticated_user_cannot_access_role2_content(self, client: AsyncClient):
        response = await client.get('/content/role2')
        assert response.status_code == 401


class TestAdminExclusiveContent:

    @pytest.mark.asyncio
    async def test_admin_can_access_admin_content(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'admin',
            'password': 'adminpass'
        })
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = await client.get('/content/admin', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert 'admin' in data['content'].lower()

    @pytest.mark.asyncio
    async def test_role1_cannot_access_admin_content(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'alice',
            'password': 'alicepass'
        })
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = await client.get('/content/admin', headers=headers)
        assert response.status_code == 403
        assert 'missing permissions' in response.text.lower()

    @pytest.mark.asyncio
    async def test_role2_cannot_access_admin_content(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'bob',
            'password': 'bobpass'
        })
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = await client.get('/content/admin', headers=headers)
        assert response.status_code == 403
        assert 'missing permissions' in response.text.lower()


class TestInvalidTokenForContent:

    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self, client: AsyncClient):
        headers = {'Authorization': 'Bearer invalid.token'}
        response = await client.get('/content/common', headers=headers)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_revoked_token_rejected(self, client: AsyncClient):
        login_response = await client.post('/login', json={
            'username': 'alice',
            'password': 'alicepass'
        })
        token = login_response.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        response = await client.get('/content/common', headers=headers)
        assert response.status_code == 200

        await client.post('/logout', data={'token': token})

        response = await client.get('/content/common', headers=headers)
        assert response.status_code == 401
