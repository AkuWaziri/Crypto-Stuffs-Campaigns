from datetime import datetime, timedelta, timezone

from freshness import age_seconds, is_within_window


def test_five_minute_signal_is_fresh():
    now = datetime.now(timezone.utc)
    published = now - timedelta(minutes=4, seconds=59)
    assert is_within_window(published, max_age_minutes=5, now=now)


def test_signal_at_boundary_is_fresh():
    now = datetime.now(timezone.utc)
    published = now - timedelta(minutes=5)
    assert is_within_window(published, max_age_minutes=5, now=now)


def test_old_signal_is_rejected():
    now = datetime.now(timezone.utc)
    published = now - timedelta(minutes=5, seconds=1)
    assert not is_within_window(published, max_age_minutes=5, now=now)


def test_future_timestamp_is_not_negative_age():
    now = datetime.now(timezone.utc)
    published = now + timedelta(minutes=1)
    assert age_seconds(published, now) == 0.0
