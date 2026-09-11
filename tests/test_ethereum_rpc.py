import json

import pytest

from ethereum_rpc import EthereumRPCClient, EthereumRPCResponseError


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def test_chain_id(monkeypatch):
    monkeypatch.setattr(
        "ethereum_rpc.urllib.request.urlopen",
        lambda request, timeout: FakeResponse({"jsonrpc": "2.0", "id": 1, "result": "0x1"}),
    )
    assert EthereumRPCClient("https://example.invalid").chain_id() == 1


def test_reads_are_cached(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append(1)
        return FakeResponse({"jsonrpc": "2.0", "id": 1, "result": "0x123"})

    monkeypatch.setattr("ethereum_rpc.urllib.request.urlopen", fake_urlopen)
    client = EthereumRPCClient("https://example.invalid", cache_ttl_seconds=60)
    assert client.get_block_number() == 0x123
    assert client.get_block_number() == 0x123
    assert len(calls) == 1


def test_rpc_error_is_not_safe(monkeypatch):
    monkeypatch.setattr(
        "ethereum_rpc.urllib.request.urlopen",
        lambda request, timeout: FakeResponse({"jsonrpc": "2.0", "id": 1, "error": {"code": -32000}}),
    )
    with pytest.raises(EthereumRPCResponseError):
        EthereumRPCClient("https://example.invalid").get_block_number()


def test_execution_is_forbidden():
    client = EthereumRPCClient("https://example.invalid")
    with pytest.raises(ValueError, match="forbidden"):
        client.call("eth_sendRawTransaction", ["0xdead"])


def test_logs_must_be_a_list(monkeypatch):
    monkeypatch.setattr(
        "ethereum_rpc.urllib.request.urlopen",
        lambda request, timeout: FakeResponse({"jsonrpc": "2.0", "id": 1, "result": {}}),
    )
    with pytest.raises(EthereumRPCResponseError, match="non-list"):
        EthereumRPCClient("https://example.invalid").get_logs({})
