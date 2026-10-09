from classifier import classify, is_relevant


def test_security_finding_is_relevant():
    item = classify({"source": "x", "text": "Bitcoin exploit investigation traced stolen funds"})
    assert is_relevant(item)
    assert "security" in item["types"]
    assert "finding" in item["types"]


def test_airdrop_is_relevant():
    item = classify({"source": "x", "text": "Join this crypto airdrop campaign"})
    assert is_relevant(item)
    assert "airdrop" in item["types"]


def test_hackathon_rewards_are_relevant():
    item = classify({"source": "x", "text": "Web3 hackathon with prizes for builders"})
    assert is_relevant(item)
    assert "hackathon" in item["types"]
    assert "reward" in item["types"]


def test_building_finding_is_relevant():
    item = classify({"source": "reddit", "text": "Ethereum developer tool release"})
    assert is_relevant(item)
    assert "build" in item["types"]


def test_non_crypto_post_is_not_relevant():
    item = classify({"source": "reddit", "text": "Funny joke about football"})
    assert not is_relevant(item)
