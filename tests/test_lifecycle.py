from datetime import datetime, timezone

from feedback import make_feedback
from launch_engine import prepare_launch_request
from post_launch import LaunchObservation, summarize_observations
from token_concept import TokenConcept


def test_launch_is_disabled_by_default():
    concept = TokenConcept("n1", "Dogecoin Payments", "DOGE", "thesis", ("s1",))
    assert prepare_launch_request(concept) is None


def test_post_launch_summary_and_feedback_are_read_only():
    now = datetime.now(timezone.utc)
    observations = [
        LaunchObservation("mint", now, liquidity_usd=100_000, volume_usd=250_000, holders=500, creator_fees_usd=5),
        LaunchObservation("mint", now, liquidity_usd=200_000, volume_usd=500_000, holders=800, creator_fees_usd=10),
    ]
    snapshot = summarize_observations("mint", observations)
    feedback = make_feedback("n1", "mint", snapshot)
    assert snapshot.peak_volume_usd == 500_000
    assert snapshot.peak_liquidity_usd == 200_000
    assert snapshot.peak_holders == 800
    assert snapshot.total_creator_fees_usd == 15
    assert feedback.outcome_score > 0
