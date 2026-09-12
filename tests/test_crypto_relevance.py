from crypto_relevance import is_crypto_relevant


def test_rejects_crypto_publication_with_non_crypto_story():
    assert not is_crypto_relevant(
        "ChatGPT Images 2.5 vs Nano Banana 2: Which One is Better?",
        "OpenAI's new image model promises sharper detail and more precise editing.",
    )


def test_accepts_direct_crypto_story():
    assert is_crypto_relevant(
        "Solana launches new stablecoin payment rails",
        "The protocol expands USDC payments across Solana wallets.",
    )


def test_accepts_ai_crypto_story():
    assert is_crypto_relevant(
        "New AI agent launches on Base",
        "The crypto agent can execute onchain tasks through a smart contract.",
    )
