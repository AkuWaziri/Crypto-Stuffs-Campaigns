from xstocks_provider import _extract_assets, verified_preferred_stocks


class FakeProvider:
    def __init__(self, assets):
        self.assets = assets

    def list_assets(self):
        return self.assets


def test_extracts_assets_from_data_wrapper():
    payload = {"data": [{"symbol": "AAPLx", "name": "Apple xStock"}]}
    assert _extract_assets(payload)[0]["symbol"] == "AAPLx"


def test_verifies_only_live_preferred_xstocks():
    provider = FakeProvider(
        [
            {"symbol": "AAPLx", "name": "Apple xStock"},
            {"symbol": "NVDAx", "name": "NVIDIA xStock"},
            {"symbol": "NOTx", "name": "Not preferred"},
        ]
    )
    result = verified_preferred_stocks(provider)
    assert {item.symbol for item in result} == {"AAPLX", "NVDAX"}
    assert all(item.availability == "live-verified" for item in result)


def test_fails_closed_when_no_preferred_asset_is_live():
    provider = FakeProvider([{"symbol": "NOTx", "name": "Not preferred"}])
    try:
        verified_preferred_stocks(provider)
    except ValueError as exc:
        assert "no preferred tokenized-stock asset" in str(exc)
    else:
        raise AssertionError("expected ValueError")
