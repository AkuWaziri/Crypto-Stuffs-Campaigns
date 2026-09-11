import pytest

from evm_chain import EVMChainConfig, arc_mainnet_chain, arc_testnet_chain, ethereum_chain


def test_ethereum_chain_config():
    chain = ethereum_chain("https://example.invalid/rpc")
    assert chain.chain_id == 1
    assert chain.native_symbol == "ETH"
    assert chain.dexscreener_chain_id == "ethereum"
    chain.validate()


def test_arc_testnet_is_distinct_from_arc_mainnet():
    testnet = arc_testnet_chain("https://example.invalid/arc-testnet")
    mainnet = arc_mainnet_chain("https://example.invalid/arc-mainnet")
    assert testnet.chain_id == 5042002
    assert mainnet.chain_id == 5042
    assert testnet.chain_id != mainnet.chain_id
    assert testnet.native_symbol == "USDC"
    assert mainnet.native_symbol == "USDC"


def test_evm_chain_requires_rpc():
    chain = EVMChainConfig(name="Example", chain_id=123, rpc_url="", native_symbol="ETH")
    with pytest.raises(ValueError, match="RPC URL"):
        chain.validate()
