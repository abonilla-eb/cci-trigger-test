import unittest
from parameterized import parameterized

from server.factory_event_server import FactoryServerEvent
from server.server_event import (
    AcceptChallenge,
    Movements,
    AbortGame,
    ListUsers,
    Challenge
)

from server.constants import (
    ACCEPT_CHALLENGE,
    LIST_USERS,
    ABORT_GAME,
    ASK_CHALLENGE
)


class TestFactoryServerEvent(unittest.TestCase):
    @parameterized.expand([
        ({'action': ACCEPT_CHALLENGE}, ),
        ({'action': ABORT_GAME}, ),
        ({'action': LIST_USERS}, ),
        ({'action': ASK_CHALLENGE}, ),
    ])
    def test_factory_server_event(self, data):
        client = 'client'
        EVENT = {
            ACCEPT_CHALLENGE: AcceptChallenge,
            LIST_USERS: ListUsers,
            ABORT_GAME: AbortGame,
            ASK_CHALLENGE: Challenge
        }
        event = FactoryServerEvent().get_event(data, client)
        event_server = EVENT.get(data.get('action'), Movements)
        self.assertIsInstance(event, event_server)
