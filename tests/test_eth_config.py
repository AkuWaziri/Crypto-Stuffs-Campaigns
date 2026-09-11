import pytest

from eth_config import EthereumConfig


def test_mainnet_config_is_valid():
    EthereumConfig(rpc_url="https://example.invalid").validate()


def test_non_mainnet_is_rejected():
    with pytest.raises(ValueError, match="mainnet"):
        EthereumConfig(chain_id=137, rpc_url="https://example.invalid").validate()


def test_missing_rpc_is_rejected():
    with pytest.raises(ValueError, match="ETH_RPC_URL"):
        EthereumConfig(rpc_url="").validate()
