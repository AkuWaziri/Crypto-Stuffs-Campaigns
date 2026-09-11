from live_observation import Observation
from telegram_output import format_feed

def test_telegram_feed_contains_manual_only_boundary():
    obs=Observation("TEST","Token","0x1111111111111111111111111111111111111111","dex",100000,50000,80,"RESEARCH NOW",(),(),("SIGNAL",),"https://example.com")
    text=format_feed([obs])
    assert "READ-ONLY" in text
    assert "No trades" in text
    assert "TEST" in text
