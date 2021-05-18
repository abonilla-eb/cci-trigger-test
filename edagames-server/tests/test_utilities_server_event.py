import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from parameterized import parameterized

from server.utilities_server_event import (
    ServerEvent,
    make_challenge,
    make_move,
    make_penalize,
    make_end_data_for_web,
)
from server.exception import GameIdException

from server.constants import (
    DEFAULT_GAME,
    TIME_SLEEP,
    TIME_CHALLENGE,
    BOARD_ID,
    TURN_TOKEN,
    PREFIX_TURN_TOKEN,
    PREFIX_CHALLENGE,
)


class TestMakeFunctions(unittest.IsolatedAsyncioTestCase):

    @patch('server.utilities_server_event.notify_challenge_to_client')
    @patch('server.utilities_server_event.save_string')
    async def test_make_challenge(self, mock_save, mock_notify):
        challenge_id = 'test_challenge_id'
        challenger = 'Pedro'
        challenged = 'Pablo'
        players = [challenger, challenged]
        data_challenge = 'test_data_challenge'
        with patch('server.utilities_server_event.identifier', return_value=challenge_id) as mock_identifier:
            with patch('server.utilities_server_event.data_challenge', return_value=data_challenge) as mock_data:
                await make_challenge(players)
                mock_identifier.assert_called_once_with()
                mock_data.assert_called_once_with(players, DEFAULT_GAME)
                mock_save.assert_called_once_with(
                    PREFIX_CHALLENGE + challenge_id,
                    data_challenge,
                    TIME_CHALLENGE,
                )
                mock_notify.assert_awaited_once_with(
                    challenged,
                    challenger,
                    challenge_id,
                )

    @patch('server.utilities_server_event.notify_your_turn')
    async def test_make_move(self, mock_notify_your_turn):
        game_id = 'test_game_id'
        token_turn = 'c303282d'
        current_player = 'Pablo'
        turn_data = {}
        data = MagicMock(
            game_id=game_id,
            current_player=current_player,
            turn_data=turn_data
        )
        with patch('server.utilities_server_event.next_turn', return_value=token_turn) as mock_next_turn:
            res = await make_move(data)
            mock_next_turn.assert_called_once_with(game_id)
            self.assertEqual(data.turn_data, {BOARD_ID: game_id, TURN_TOKEN: token_turn})
            mock_notify_your_turn.assert_awaited_once_with(
                current_player,
                turn_data,
            )
            self.assertEqual(res, token_turn)

    @patch('server.utilities_server_event.make_move')
    @patch('server.utilities_server_event.GRPCAdapterFactory.get_adapter')
    @patch('server.utilities_server_event.asyncio.sleep')
    async def test_make_penalize_called(self, mock_sleep, gadapter_patched, mock_move):
        player_1 = 'Pedro'
        player_2 = 'Pablo'
        game_id = '123987'
        turn_token = 'turn_token'
        data = MagicMock(
            game_id=game_id,
            current_player=player_1,
        )
        game_name = DEFAULT_GAME
        adapter_patched = AsyncMock()
        adapter_patched.penalize.return_value = MagicMock(
            game_id=game_id,
            current_player=player_2,
        )
        gadapter_patched.return_value = adapter_patched
        with patch('server.utilities_server_event.get_string', return_value=turn_token) as mock_get:
            await make_penalize(data, game_name, turn_token)
            mock_sleep.assert_awaited_once_with(TIME_SLEEP)
            mock_get.assert_awaited_once_with(
                f'{PREFIX_TURN_TOKEN}{game_id}',
                player_1,
                TURN_TOKEN,
            )
            gadapter_patched.assert_called_with(DEFAULT_GAME)
            mock_move.assert_awaited_once_with(adapter_patched.penalize.return_value)

    @patch('server.utilities_server_event.make_move')
    @patch('server.utilities_server_event.GRPCAdapterFactory.get_adapter')
    @patch('server.utilities_server_event.asyncio.sleep')
    async def test_make_penalize_not_called(self, mock_sleep, gadapter_patched, mock_move):
        player_1 = 'Pedro'
        game_id = '123987'
        turn_token_1 = 'turn_token_1'
        turn_token_2 = 'turn_token_2'
        data = MagicMock(
            game_id=game_id,
            current_player=player_1,
        )
        game_name = DEFAULT_GAME
        with patch('server.utilities_server_event.get_string', return_value=turn_token_2) as mock_get:
            await make_penalize(data, game_name, turn_token_1)
            mock_sleep.assert_awaited_once_with(TIME_SLEEP)
            mock_get.assert_awaited_once_with(
                f'{PREFIX_TURN_TOKEN}{game_id}',
                player_1,
                TURN_TOKEN,
            )
            gadapter_patched.assert_not_called()
            mock_move.assert_not_called()

    @parameterized.expand([
        # Dicctionary in order
        (
            {
                'player_1': 'pedro',
                'player_2': 'pablo',
                'game_id': 'f932jf',
                'score_1': 1000,
                'score_2': 2000,
                'remaining_moves': 130,
            },
            [('pedro', 1000), ('pablo', 2000)],
        ),
        # untidy players in dicctionary
        (
            {
                'player_2': 'pablo',
                'player_1': 'pedro',
                'game_id': 'f932jf',
                'score_1': 1000,
                'score_2': 2000,
                'remaining_moves': 130,
            },
            [('pablo', 2000), ('pedro', 1000)],

        ),
    ])
    def test_make_end_data_for_web(self, data, expected):
        res = make_end_data_for_web(data)
        self.assertEqual(res, expected)


class TestServerEvent(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.client = 'test_client'

    @parameterized.expand([
        ({"action": "accept_challenge", "data": {"game_id": "c303282d-f2e6-46ca-a04a-35d3d873712d"}},),
    ])
    async def test_search_value(self, response):
        value_expected = "c303282d-f2e6-46ca-a04a-35d3d873712d"
        value = 'game_id'
        value_search = await ServerEvent(response, self.client).search_value(value)
        self.assertEqual(value_search, value_expected)

    @parameterized.expand([
        ({"action": "accept_challenge", "data": {}},),
    ])
    async def test_search_value_error(self, response):
        with patch('server.utilities_server_event.notify_error_to_client') as notify_patched:
            value = 'game_id'
            await ServerEvent(response, self.client).search_value(value)
            notify_patched.assert_called_once_with(self.client, str(GameIdException))

    @patch('asyncio.create_task')
    @patch('server.utilities_server_event.make_penalize', new_callable=MagicMock, return_value='ret_penalize')
    @patch('server.utilities_server_event.make_move', return_value='test_token')
    async def test_move(
        self,
        mock_make_move,
        mock_make_penalize,
        mock_asyncio,
    ):
        data = MagicMock(
            game_id='123987',
            current_player='Pedro',
            turn_data={},
        )
        game_name = DEFAULT_GAME
        await ServerEvent({}, self.client).move(data, game_name)
        mock_make_move.assert_awaited_once_with(data)
        mock_make_penalize.assert_called_once_with(data, game_name, 'test_token')
        mock_asyncio.assert_called_once_with('ret_penalize')

    @patch('server.utilities_server_event.notify_end_game_to_web')
    @patch('server.utilities_server_event.notify_end_game_to_client')
    @patch('server.utilities_server_event.next_turn')
    async def test_game_over(self, mock_next, mock_notify_end_to_client, mock_notify_end_to_web):
        players = ['Pedro', 'Pablo']
        game_data = {
            'players': players,
            'name': DEFAULT_GAME,
        }
        game_id = 'f34i3f'
        turn_data = 'test_turn_data'
        data = MagicMock(
            game_id=game_id,
            turn_data=turn_data,
        )
        test_end_data = 'test_end_data'
        with patch('server.utilities_server_event.make_end_data_for_web', return_value=test_end_data) as mock_end_data:
            await ServerEvent({}, self.client).game_over(data, game_data)
            mock_next.assert_called_once_with(game_id)
            mock_end_data.assert_called_once_with(turn_data)
            mock_notify_end_to_client.assert_called_once_with(players, turn_data)
            mock_notify_end_to_web.assert_called_once_with(game_id, test_end_data)
