from classifier import classify, is_relevant

def test_satirical_crypto_item_is_relevant():
    item = classify({"source": "x", "text": "Bitcoin satire about the market"})
    assert is_relevant(item)
    assert "satire" in item["types"]

def test_research_finding_is_relevant():
    item = classify({"source": "reddit", "text": "Ethereum research findings from a new study"})
    assert is_relevant(item)
    assert "research" in item["types"]
    assert "finding" in item["types"]

def test_crypto_campaign_is_relevant():
    item = classify({"source": "x", "text": "Join this crypto airdrop campaign"})
    assert is_relevant(item)
    assert "airdrop" in item["types"]

def test_hackathon_is_relevant():
    item = classify({"source": "x", "text": "Web3 hackathon with prizes for builders"})
    assert is_relevant(item)
    assert "hackathon" in item["types"]
    assert "reward" in item["types"]

def test_video_campaign_is_relevant():
    item = classify({"source": "reddit", "text": "Crypto video challenge: make a short explainer"})
    assert is_relevant(item)
    assert "video" in item["types"]

def test_non_crypto_joke_is_not_relevant():
    item = classify({"source": "reddit", "text": "Funny joke about football"})
    assert not is_relevant(item)
