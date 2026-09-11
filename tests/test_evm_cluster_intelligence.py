from evm_cluster_intelligence import inspect_address_clusters

def test_cluster_detects_early_buyer_funding_overlap():
    a="0x1111111111111111111111111111111111111111"
    b="0x2222222222222222222222222222222222222222"
    report=inspect_address_clusters(early_buyer_addresses=[a], funding_sender_addresses=[a,b])
    assert report.overlap_count == 1
    assert "EARLY_BUYER_FUNDING_OVERLAP" in report.signals

def test_cluster_is_observational_when_empty():
    report=inspect_address_clusters()
    assert "NO_CLUSTER_ADDRESSES" in report.warnings
