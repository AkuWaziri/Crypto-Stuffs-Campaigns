import pytest

from evm_funding_intelligence import (
    TRANSFER_TOPIC,
    FundingValidationError,
    inspect_funding,
)

TOKEN = "0x1111111111111111111111111111111111111111"
ANCHOR = "0x2222222222222222222222222222222222222222"
FUNDER = "0x3333333333333333333333333333333333333333"
BUYER = "0x4444444444444444444444444444444444444444"


def word(address):
    return "0x" + ("0" * 24) + address[2:]


def uint(value):
    return "0x" + f"{value:064x}"


def log(sender, receiver, block, amount, tx_hash):
    return {
        "topics": [TRANSFER_TOPIC, word(sender), word(receiver)],
        "data": uint(amount),
        "blockNumber": hex(block),
        "transactionHash": tx_hash,
    }


def test_funding_report_collects_anchor_inbound_and_outbound_flow():
    class FakeRPC:
        def get_logs(self, params, use_cache=True):
            assert params["address"] == TOKEN
            assert params["topics"] == [TRANSFER_TOPIC]
            return [
                log(FUNDER, ANCHOR, 100, 500, "0xaaa"),
                log(ANCHOR, BUYER, 110, 200, "0xbbb"),
                log(BUYER, BUYER, 120, 999, "0xccc"),
            ]

    report = inspect_funding(FakeRPC(), TOKEN, [ANCHOR], 90, 130)

    assert report.observed_transfers == 2
    assert report.inbound_count == 1
    assert report.outbound_count == 1
    assert report.unique_senders == (FUNDER,)
    assert report.unique_receivers == (BUYER,)
    assert report.transfers[0].amount == 500
    assert "FUNDING_DATA_IS_TOKEN_FLOW_EVIDENCE" in report.warnings


def test_funding_report_rejects_empty_anchor_set():
    class FakeRPC:
        pass

    with pytest.raises(FundingValidationError):
        inspect_funding(FakeRPC(), TOKEN, [], 1, 2)
