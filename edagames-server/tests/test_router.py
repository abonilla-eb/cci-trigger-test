import unittest
from unittest.mock import patch
from parameterized import parameterized
from httpx import AsyncClient

from server.server import app, manager


class TestRouter(unittest.IsolatedAsyncioTestCase):
    @parameterized.expand([
        ({"challenger": "Ana", "challenged": "Pepe", "challenge_id": "2138123721"}, 200),
    ])
    async def test_challenge(self, data, status):
        with patch('server.router.make_challenge') as mock_make_challenge:
            async with AsyncClient(app=app, base_url="http://test") as ac:
                response = await ac.post(
                    "/challenge",
                    json=data
                )
        mock_make_challenge.assert_awaited_once_with(['Ana', 'Pepe'])
        self.assertEqual(response.status_code, status)
        self.assertEqual(response.json(), data)

    async def test_update_users_in_django(self):
        user_list = {"users": ["User 1"]}
        user_dict = {'User 1': 'websockets'}

        manager.connections = user_dict

        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/users")

        assert response.status_code == 200
        assert response.json() == user_list
