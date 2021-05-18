from server.server_event import (
    AcceptChallenge,
    Movements,
    ListUsers,
    Challenge,
    AbortGame
)

from server.constants import (
    ACCEPT_CHALLENGE,
    LIST_USERS,
    ASK_CHALLENGE,
    ABORT_GAME,
)


EVENT = {
    ACCEPT_CHALLENGE: AcceptChallenge,
    LIST_USERS: ListUsers,
    ASK_CHALLENGE: Challenge,
    ABORT_GAME: AbortGame,
}


class FactoryServerEvent(object):
    @staticmethod
    def get_event(data, client):
        event = EVENT.get(data.get('action'), Movements)
        return event(data, client)
