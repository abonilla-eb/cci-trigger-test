import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from parameterized import parameterized

from server.server_event import (
    ListUsers,
    Challenge,
    AcceptChallenge,
    Movements,
    AbortGame,
)
from server.utilities_server_event import ServerEvent

from server.constants import (
    EMPTY_PLAYER,
    OPPONENT,
    CHALLENGE_ID,
    DEFAULT_GAME,
    PREFIX_CHALLENGE,
    PREFIX_GAME,
)


class TestServerEvent(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.uuid = 'c303282d-f2e6-46ca-a04a-35d3d873712d'
        self.client = 'Player 1'

    async def test_ListUsers_run(self):
        data = {'action': 'list_users'}
        users = [self.client, 'User 2', 'User 3']
        with patch('server.server_event.notify_user_list_to_client', new_callable=AsyncMock) as notify_patched,\
                patch('server.server_event.manager') as manager_patched:
            manager_patched.connections.keys.return_value = users
            await ListUsers(data, self.client).run()
            notify_patched.assert_called_with(self.client, users)

    @patch('server.server_event.make_challenge')
    async def test_Challenge_run(self, mock_make_challenge):
        opponent = 'test_opponent'
        response = {'data': {'opponent': opponent}}
        with patch.object(ServerEvent, 'search_value', return_value=opponent) as mock_search:
            await Challenge(response, self.client).run()
            mock_search.assert_awaited_once_with(OPPONENT)
            mock_make_challenge.assert_awaited_once_with([self.client, opponent])

    @patch.object(AcceptChallenge, 'start_game')
    async def test_AcceptChallenge_run(self, mock_start):
        data = {"action": "accept_challenge", "data": {"challenge_id": "c303282d-f2e6-46ca-a04a-35d3d873712d"}}
        challenge_id = 'challenge_id_from_request'
        get_redis = 'data_from_redis'
        json_to_python = 'python data'
        with patch.object(ServerEvent, 'search_value', return_value=challenge_id) as mock_search:
            with patch('server.server_event.get_string', return_value=get_redis) as mock_get:
                with patch('json.loads', return_value=json_to_python) as mock_json:
                    await AcceptChallenge(data, self.client).run()
                    mock_search.assert_awaited_once_with(CHALLENGE_ID)
                    mock_get.assert_awaited_once_with(
                        f'{PREFIX_CHALLENGE}{challenge_id}',
                        self.client,
                        CHALLENGE_ID,
                    )
                    mock_json.assert_called_with(get_redis)
                    mock_start.assert_called_with(json_to_python)

    @patch.object(ServerEvent, 'move')
    @patch('server.server_event.save_string')
    async def test_AcceptChallenge_start_game(self, mock_save, mock_move):
        game_id = 'asd123'
        game_data = {
            'name': DEFAULT_GAME,
            'players': ['client1', 'clint2'],
        }
        with patch('server.server_event.GRPCAdapterFactory.get_adapter', new_callable=AsyncMock) as g_adapter_patched:
            adapter_patched = AsyncMock()
            adapter_patched.create_game.return_value = MagicMock(
                game_id=game_id,
                current_player='client1',
                turn_data={},
                play_data={},
            )
            g_adapter_patched.return_value = adapter_patched
            data_json = 'json response'
            with patch('json.dumps', return_value=data_json) as mock_json:
                await AcceptChallenge({}, 'client1').start_game(game_data)
                g_adapter_patched.assert_called_with(DEFAULT_GAME)
                mock_json.assert_called_once_with(game_data)
                mock_save.assert_called_once_with(
                    f'{PREFIX_GAME}{game_id}',
                    data_json,
                )
                mock_move.assert_awaited_once_with(
                    adapter_patched.create_game.return_value,
                    DEFAULT_GAME,
                )

    async def test_Movements_run(self):
        client = 'Test Client 1'
        data = {
            "action": "accept_challenge",
            "data": {"turn_token": "303282d-f2e6-46ca-a04a-35d3d873712d", "board_id": 'c303282d'},
        }
        with patch.object(ServerEvent, 'search_value', return_value='value') as mock_search:
            with patch("server.server_event.get_string", return_value='value') as mock_get:
                with patch('json.loads', return_value='json_value') as mock_json:
                    with patch.object(Movements, 'execute_action', return_value='value') as mock_execute:
                        await Movements(data, client).run()
                        mock_search.assert_called()
                        mock_get.assert_called()
                        mock_json.asseer_called()
                        mock_execute.assert_called()

    @patch.object(ServerEvent, 'move')
    async def test_Movements_execute_action(self, mock_move):
        client = 'client1'
        game_data = {'name': DEFAULT_GAME, 'players': [client, 'client2']}
        game_id = 'test_game_id'
        turn_data = {'player_1': client, 'score_1': 1000, 'player_2': 'client2', 'score_2': 500}
        with patch('server.server_event.GRPCAdapterFactory.get_adapter', new_callable=AsyncMock) as Gadapter_patched,\
                patch.object(Movements, 'log_action') as log_patched:
            adapter_patched = AsyncMock()
            adapter_patched.execute_action.return_value = MagicMock(
                turn_data=turn_data,
                current_player=client,
                game_id=game_id,
            )
            Gadapter_patched.return_value = adapter_patched
            await Movements({}, client).execute_action(game_data, game_id)
            Gadapter_patched.assert_called_with(DEFAULT_GAME)
            log_patched.assert_awaited_once_with(
                adapter_patched.execute_action.return_value,
            )
            mock_move.assert_awaited_once_with(
                adapter_patched.execute_action.return_value,
                DEFAULT_GAME,
            )

    @patch.object(ServerEvent, 'game_over')
    async def test_Movements_end_game(self, mock_game_over):
        client = 'client1'
        game_data = {'name': DEFAULT_GAME, 'players': '[client1 ,clint1]'}
        game_id = 'test_game_id'
        turn_data = {'player_1': 'client1', 'score_1': 1000, 'player_2': 'client2', 'score_2': 500}
        with patch('server.server_event.GRPCAdapterFactory.get_adapter') as g_adapter_patched,\
                patch.object(Movements, 'log_action'):
            adapter_patched = AsyncMock()
            adapter_patched.execute_action.return_value = MagicMock(
                turn_data=turn_data,
                current_player=EMPTY_PLAYER,
            )
            g_adapter_patched.return_value = adapter_patched
            await Movements({}, client).execute_action(game_data, game_id)
            mock_game_over.assert_awaited_once_with(
                adapter_patched.execute_action.return_value,
                game_data,
            )

    @patch('server.server_event.save_string')
    @patch('json.dumps')
    async def test_movements_log_action(self, json_dumps_patched, save_patched):
        data = MagicMock(
            game_id='test-0000-00000001',
            previous_player='Player1',
            turn_data={
                'board_id': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                'action': 'move',
                'from_row': 3,
                'from_col': 4,
                'to_row': 4,
                'to_col': 4,
            },
        )
        turn_data_json = (
            '{"turn": "Player1", "data": {'
            '"board_id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", '
            '"action": "move", '
            '"from_row": 3, '
            '"from_col": 4, '
            '"to_row": 4, '
            '"to_col": 4'
            '}}'
        )
        json_dumps_patched.return_value = turn_data_json
        await Movements({}, 'client').log_action(data)
        save_patched.assert_called_once_with(
            'l_test-0000-00000001',
            turn_data_json,
        )

    @parameterized.expand([
        (
            {
                "action": "accept_challenge",
                "data": {"turn_token": "303282d-f2e6-46ca-a04a-35d3d873712d", "board_id": 'c303282d'}
            },
        ),
    ])
    async def test_AbortGame_run(self, data):
        client = 'Test Client'
        with patch.object(ServerEvent, 'search_value', return_value='10') as mock_search:
            with patch('server.server_event.get_string', return_value='10') as mock_get:
                with patch.object(AbortGame, 'end_game', return_value='10') as mock_end:
                    await AbortGame(data, client).run()
                    mock_search.assert_any_call('board_id')
                    mock_search.assert_any_call('turn_token')
                    self.assertEqual(mock_search.call_count, 2)
                    mock_get.assert_awaited()
                    mock_end.assert_awaited()

    @patch.object(ServerEvent, 'game_over')
    async def test_AbortGame_end_game(self, mock_game_over):
        client = 'client'
        game_id = 'asd123'
        with patch('server.server_event.GRPCAdapterFactory.get_adapter') as g_adapter_patched:
            adapter_patched = AsyncMock()
            adapter_patched.end_game.return_value = MagicMock(
                current_player=EMPTY_PLAYER,
                turn_data={'player_1': 'Mark', 'score_1': 1000},
                play_data={'state': 'game_over'}
            )
            g_adapter_patched.return_value = adapter_patched
            game = {'name': DEFAULT_GAME, 'players': '[client1 ,clint1]'}
            await AbortGame({}, client).end_game(game, game_id)
            mock_game_over.assert_awaited_once_with(
                adapter_patched.end_game.return_value,
                game,
            )
