from evm_monitor import parse_rpc_transfer_log, parse_swap_transfer


def test_evm_buy_is_classified():
    event = parse_swap_transfer(
        {"type": "SWAP", "receivedTarget": True, "spentTarget": False, "hash": "0x1"},
        "0xwallet",
        asset="TOKEN",
        value_usd=100000,
    )
    assert event is not None
    assert event.action == "BUY"
    assert event.value_usd == 100000


def test_plain_transfer_is_not_called_a_buy():
    event = parse_rpc_transfer_log({"tokenTransfer": True, "transactionHash": "0x2"}, "0xwallet", asset="TOKEN")
    assert event is not None
    assert event.action == "TRANSFER"
