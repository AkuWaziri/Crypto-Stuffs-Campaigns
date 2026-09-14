from models import classify_crypto_flow


def test_non_swap_is_transfer():
    assert classify_crypto_flow(received_target=True, spent_target=False, is_swap=False) == "TRANSFER"


def test_target_received_is_buy():
    assert classify_crypto_flow(received_target=True, spent_target=False, is_swap=True) == "BUY"


def test_target_spent_is_sell():
    assert classify_crypto_flow(received_target=False, spent_target=True, is_swap=True) == "SELL"


def test_ambiguous_swap_is_unknown():
    assert classify_crypto_flow(received_target=True, spent_target=True, is_swap=True) == "UNKNOWN"
