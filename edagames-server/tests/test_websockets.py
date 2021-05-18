import unittest
from unittest.mock import AsyncMock, patch

from server.connection_manager import ConnectionManager
from server.websockets import (
    notify_error_to_client,
    notify_challenge_to_client,
    notify_your_turn,
    notify_user_list_to_client,
    notify_end_game_to_client,
    notify_feedback,
)

import server.constants as websocket_events


class TestWebsockets(unittest.IsolatedAsyncioTestCase):
    @patch.object(ConnectionManager, 'send', new_callable=AsyncMock)
    async def test_notify_error_to_client(self, send_patched):
        client = 'User 1'
        error = 'message error'
        await notify_error_to_client(
            client,
            error,
        )
        send_patched.assert_awaited_once_with(
            client,
            websocket_events.EVENT_SEND_ERROR,
            {
                'Error': error,
            },
        )

    @patch.object(ConnectionManager, 'send', new_callable=AsyncMock)
    async def test_notify_challenge_to_client(self, send_patched):
        challenge_sender = 'User 1'
        challenge_receiver = 'User 2'
        test_game_id = '00000000-0000-0000-0000-000000000001'
        await notify_challenge_to_client(
            challenge_receiver,
            challenge_sender,
            test_game_id,
        )
        send_patched.assert_awaited_once_with(
            challenge_receiver,
            websocket_events.EVENT_SEND_CHALLENGE,
            {
                'opponent': challenge_sender,
                'challenge_id': test_game_id,
            },
        )

    @patch.object(ConnectionManager, 'send', new_callable=AsyncMock)
    async def test_notify_your_turn(self, send_patched):
        challenge_sender = 'User 1'
        data = {"game_id": "c303282d-f2e6-46ca-a04a-35d3d873712d"}
        await notify_your_turn(
            challenge_sender,
            data
        )
        send_patched.assert_awaited_once_with(
            challenge_sender,
            websocket_events.EVENT_SEND_YOUR_TURN,
            data
        )

    @patch.object(ConnectionManager, 'send', new_callable=AsyncMock)
    async def test_notify_user_list_to_client(self, send_patched):
        client = 'User 1'
        users = ['User 1', 'User 2', 'User 3']
        await notify_user_list_to_client(client, users)
        send_patched.assert_awaited_once_with(
            client,
            websocket_events.EVENT_LIST_USERS,
            {
                'users': users,
            },
        )

    @patch.object(ConnectionManager, 'send', new_callable=AsyncMock)
    async def test_notify_end_game_to_client(self, send_patched):
        players = ['User 1', 'User 2']
        data = {'game_id': 'jf92j4-2jf', 'winner': 'User 2'}
        await notify_end_game_to_client(players, data)
        send_patched.assert_awaited_with(
            players[len(players) - 1],
            websocket_events.EVENT_GAME_OVER,
            data,
        )
        self.assertEqual(send_patched.call_count, len(players))

    @patch.object(ConnectionManager, 'send', new_callable=AsyncMock)
    async def test_notify_feedback(self, send_patched):
        client = 'User 1'
        feedback = 'id not found'
        await notify_feedback(client, feedback)
        send_patched.assert_awaited_once_with(
            client,
            websocket_events.EVENT_FEEDBACK,
            feedback,
        )
