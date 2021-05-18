import unittest
import server.server as server
from unittest.mock import MagicMock, patch, AsyncMock
import starlette


class TestServer(unittest.IsolatedAsyncioTestCase):

    async def test_session_open_close(self):
        websocket = AsyncMock()
        websocket.receive_text.side_effect = starlette.websockets.WebSocketDisconnect()

        with patch('server.server.manager', new_callable=AsyncMock) as manager_patched:
            manager_patched.connect.return_value = 'User 1'
            await server.session(websocket, 'token')
            manager_patched.connect.assert_called_with(websocket, 'token')
            manager_patched.remove_user.assert_called_with('User 1')

    async def test_session_invalid_client(self):
        websocket = MagicMock()
        websocket.close = AsyncMock()

        add_user_patched = MagicMock()
        add_user_patched.return_value = None
        server.add_user = add_user_patched

        await server.session(websocket, 'token')
