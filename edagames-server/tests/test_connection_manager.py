import unittest
import jwt
from parameterized import parameterized
from unittest.mock import MagicMock, AsyncMock, patch, call

from server.connection_manager import ConnectionManager
import server.constants as websocket_events


TEST_TOKEN_KEY = 'EDAGame$!2021'


def generate_token_invalid_signature():
    return jwt.encode({"user": "cliente 1"}, "invalid_secret", algorithm="HS256")


def generate_token_truncated():
    token = jwt.encode({"user": "cliente 2"}, TEST_TOKEN_KEY, algorithm="HS256")
    split_token = token.split('.')
    return '.'.join([t[:15] for t in split_token])


class TestConnectionManager(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.manager = ConnectionManager()

    @parameterized.expand([
        (
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyIjoiVGVzdCBDbGllbnQgMSJ9'
            '.zrXQiT77v9jnUVsZHr41HAZVDnJtRa84t8hmRVdzPck',
            'Test Client 1',
        ),
        (
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.'
            'eyJ1c2VyIjoiUGVkcm8ifQ.'
            'h85yCXGm1BdXbKKnLgOJ52vHAdGmcUpJ5gfCgjYyAJQ',
            'Pedro',
        ),
        (
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.'
            'eyJ1c2VyIjoiUGFibG8ifQ.'
            '3qIB7M-S34ALo1XQQ-7V4Zvzou3SPL5lJsWbINHOFBc',
            'Pablo',
        ),
    ])
    async def test_connect_valid(self, token, expected):
        websocket = AsyncMock()
        notify_patched = AsyncMock()
        self.manager.notify_user_list_changed = notify_patched
        with patch('server.connection_manager.JWT_TOKEN_KEY', TEST_TOKEN_KEY):
            client = await self.manager.connect(websocket, token)
        self.assertEqual(client, expected)
        websocket.accept.assert_called()
        notify_patched.assert_called()

    @parameterized.expand([
        (
            # Invalid signature
            generate_token_invalid_signature()
        ),
        (
            # Truncated token
            generate_token_truncated()
        ),
        (
            # Empty token
            '',
        ),
    ])
    async def test_connect_invalid(self, token):
        websocket = AsyncMock()
        notify_patched = AsyncMock()
        self.manager.notify_user_list_changed = notify_patched
        with patch('server.connection_manager.JWT_TOKEN_KEY', TEST_TOKEN_KEY):
            await self.manager.connect(websocket, token)
        self.assertEqual({}, self.manager.connections)
        websocket.close.assert_called()
        notify_patched.assert_not_called()

    @patch.object(ConnectionManager, 'notify_user_list_changed')
    async def test_remove_user(self, notify_patched):
        self.manager.connections = {'Test Client 1': 'websocket'}
        await self.manager.remove_user('Test Client 1')
        self.assertEqual({}, self.manager.connections)
        notify_patched.assert_called()

    @parameterized.expand([
        (
            {
                'Test Client 1': 'websocket1',
                'Test Client 2': 'websocket2',
                'Test Client 3': 'websocket3',
            },
        ),
        (
            {
                'Test Client 1': 'websocket1',
            },
        ),
        (
            {},
        ),
    ])
    async def test_broadcast(self, connections):
        event = 'event'
        data = {'data': "Test Message 1"}
        self.manager.connections = connections
        with patch.object(ConnectionManager, 'bulk_send') as bulk_send_patched:
            await self.manager.broadcast(event, data)
        bulk_send_patched.assert_called_with(
            connections.keys(),
            event,
            data,
        )

    @patch.object(ConnectionManager, '_send')
    async def test_manager_send(self, send_patched):
        user = 'User'
        event = 'event'
        data = {
            'data': 'some data',
            'other_data': 'some other data',
        }
        self.manager.connections = {user: 'user_websocket'}
        await self.manager.send(user, event, data)
        send_patched.assert_called_with(
            'user_websocket',
            event,
            data,
        )

    @parameterized.expand([
        ([],),
        (['client 1'],),
        (['client 1', 'client 2', 'client 3'],),
    ])
    async def test_manager_send_bulk(self, clients):
        connections = {
            client: f'websocket {i}' for i, client in enumerate(clients)
        }
        self.manager.connections = connections
        event = 'event'
        data = {'data': "Test Message 1"}
        with patch('asyncio.create_task') as create_task_patched,\
                patch.object(ConnectionManager, '_send', new_callable=MagicMock) as send_patched:
            await self.manager.bulk_send(clients, event, data)
        await self.manager.bulk_send(clients, event, data)
        self.assertEqual(len(create_task_patched.mock_calls), len(clients))
        send_patched.assert_has_calls(
            [call(ws, event, data) for ws in connections.values()]
        )

    @parameterized.expand([
        (
            'event',
            {'field': 'Test Message 1'},
            '{"event": "event", "data": {"field": "Test Message 1"}}',
        ),
        (
            'event',
            {'field': 'Test Message 1', 'field2': 'Other message'},
            '{"event": "event", "data": {"field": "Test Message 1", "field2": "Other message"}}',
        ),
        (
            '',
            {'field': 'Test Message 1'},
            '{"event": "", "data": {"field": "Test Message 1"}}',
        ),
        (
            'event',
            {},
            '{"event": "event", "data": {}}',
        ),
        (
            '',
            {},
            '{"event": "", "data": {}}',
        ),
    ])
    async def test_manager_send_internal(self, event, data, expected):
        websocket_patched = AsyncMock()
        await self.manager._send(
            websocket_patched,
            event,
            data,
        )
        websocket_patched.send_text.assert_called_with(expected)

    @patch.object(ConnectionManager, 'broadcast')
    async def test_notify_user_list_changed(self, broadcast_patched):
        self.manager.connections = {
            'client 1': 'websocket',
            'client 2': 'websocket',
            'client 3': 'websocket',
        }
        await self.manager.notify_user_list_changed()
        broadcast_patched.assert_called_with(
            websocket_events.EVENT_LIST_USERS,
            {
                'users': ['client 1', 'client 2', 'client 3'],
            },
        )
