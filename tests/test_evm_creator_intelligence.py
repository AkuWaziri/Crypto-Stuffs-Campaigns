from evm_creator_intelligence import inspect_creator

def test_creator_report_reads_creation_sender():
    class RPC:
        def get_transaction(self, tx): return {"from":"0x1111111111111111111111111111111111111111"}
        def get_transaction_receipt(self, tx): return {"contractAddress":"0x2222222222222222222222222222222222222222","blockNumber":"0x64"}
    report=inspect_creator(RPC(), "0x2222222222222222222222222222222222222222", "0xabc")
    assert report.creator == "0x1111111111111111111111111111111111111111"
    assert report.creation_block == 100
