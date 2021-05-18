import unittest
from unittest.mock import patch

from server.grpc_adapter import GRPCAdapterFactory, ClientGRPC, cached_adapters


class TestGRPCAdapterFactory(unittest.IsolatedAsyncioTestCase):

    async def test_get_adapter_cached(self):
        adapter_mock = ClientGRPC('test:1234')
        cached_adapters.update({'cached': adapter_mock})
        adapter = await GRPCAdapterFactory.get_adapter('cached')
        self.assertEqual(adapter, adapter_mock)
        cached_adapters.pop('cached')

    async def test_get_adapter_not_cached(self):
        with patch('server.grpc_adapter.discover_game') as discover_patched:
            await GRPCAdapterFactory.get_adapter('not cached')
            discover_patched.assert_called_with('not cached')
