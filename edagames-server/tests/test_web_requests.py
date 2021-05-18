import unittest
from unittest.mock import patch

from server.web_requests import (
    notify_end_game_to_web,
)


class TestWebRequests(unittest.IsolatedAsyncioTestCase):

    @patch('requests.post')
    async def test_notify_end_game_to_web(self, post_patched):
        game_id = "123e4567-e89b-12d3-a456-426614174000"
        data = {"player_1": 3000, "player_2": 5000}
        await notify_end_game_to_web(game_id, data)
        post_patched.assert_called()
