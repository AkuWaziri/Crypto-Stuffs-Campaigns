"""Editorial intelligence helpers for the Crypto-Stuffs-Campaigns feed.

Ranks discovered items and turns them into research angles and draft scaffolds.
Angles are hypotheses until the linked primary evidence has been checked.
"""
import re

TOPIC_RULES = [
    ("Security", ("exploit", "hack", "vulnerability", "security", "audit", "attack", "drain", "bug bounty")),
    ("Stablecoins & payments", ("stablecoin", "payments", "payment", "usdc", "usdt", "settlement", "remittance")),
    ("DeFi & markets", ("defi", "liquidity", "yield", "lending", "borrow", "dex", "trading", "market")),
    ("AI & agents", (" ai ", "agent", "llm", "model", "automation")),
    ("Developer tools", ("github", "open source", "sdk", "api", "tool", "framework", "repository", "repo", "tutorial", "guide")),
    ("On-chain research", ("onchain", "on-chain", "wallet", "transaction", "contract", "smart contract", "block explorer")),
    ("Infrastructure", ("infrastructure", "node", "layer 2", "l2", "bridge", "scaling", "rpc", "rollup")),
    ("Funding & opportunities", ("grant", "funding", "hackathon", "airdrop", "incentive", "rewards", "points")),
]

ANGLE_PLAYBOOK = {
    "Security": (
        "Mechanism: identify the exact permission, validation gap, or failure path; separate root cause from visible loss.",
        "Second order: ask which other contracts, integrations, or user habits share the same failure mode.",
        "Builder lens: propose a reproducible test or monitoring check that could catch this class of issue earlier.",
        "A security headline is only the symptom. The useful analysis is the failure path: [verified root cause]. If [specific condition] exists elsewhere, [system/user group] may face a similar risk. Evidence: [trace/code/advisory]. Caveat: [scope or uncertainty]."
    ),
    "Stablecoins & payments": (
        "Mechanism: map the full path from sender to recipient, including network, conversion, fees, liquidity, and settlement.",
        "Second order: explain which users or businesses could change behavior if the cost/reliability claim holds.",
        "Builder lens: measure the same transfer across routes and publish fees, completion time, and failure rate.",
        "The headline says [verified change]. For a real user, the important metric is not just the announcement; it is [total cost / settlement time / failure rate] across the full route. Compare [route A] with [route B] before calling this an improvement. The unanswered question is [limitation]."
    ),
    "DeFi & markets": (
        "Mechanism: identify where yield, liquidity, leverage, or incentives actually come from and who bears the cost.",
        "Second order: test whether growth is organic usage or temporarily subsidized activity.",
        "Builder lens: compare utilization, net incentives, liquidity depth, and downside behavior over the same period.",
        "The number to watch is [verified metric], but it does not tell the whole story. Check it against [utilization / net incentives / liquidity depth] to see whether activity is durable or subsidized. If [condition] changes, [user group] could feel it first. Missing data: [caveat]."
    ),
    "AI & agents": (
        "Mechanism: show the actual workflow the agent can complete, what tools/permissions it needs, and where a human remains necessary.",
        "Second order: ask whether this removes a real bottleneck or merely adds a chat interface to an existing process.",
        "Builder lens: reproduce one end-to-end task and report latency, cost, failure cases, and required permissions.",
        "Ignore the agent label for a moment. The test is whether it can complete [specific task] with [required tools/permissions], at [measured cost/time], without [failure mode]. If it can, the useful unlock is [workflow change]. What still needs proving: [limitation]."
    ),
    "Developer tools": (
        "Mechanism: install or run the tool and identify the exact developer step it removes or simplifies.",
        "Second order: explain what becomes easier to build, integrate, or maintain because this exists.",
        "Builder lens: make a tiny reproducible demo and document setup time, limitations, and one realistic use case.",
        "I would not judge this by the launch post. The useful test is whether [tool/SDK] makes [specific task] materially simpler. Build a minimal example, measure [setup time / calls / errors], and compare it with [current approach]. If it holds up, it could unlock [specific builder use case]."
    ),
    "On-chain research": (
        "Mechanism: trace the transaction or contract call and separate what the data proves from what it merely suggests.",
        "Second order: identify a behavior, incentive, or dependency invisible in the headline.",
        "Builder lens: turn the finding into a reproducible query, dashboard, or alert with a timestamped data source.",
        "The interesting part is not the wallet label; it is the behavior visible in [transaction/event/contract call]. The data supports [verified observation], but does not yet prove [common assumption]. To test the thesis, compare [addresses/events/time window] and watch [metric]."
    ),
    "Infrastructure": (
        "Mechanism: explain which bottleneck changes, under what assumptions, and what trade-off is introduced.",
        "Second order: connect the change to developer experience, application economics, reliability, or composability.",
        "Builder lens: benchmark one real workload and publish configuration, latency/cost, and failure cases.",
        "The claim matters only if it changes [latency / cost / throughput / reliability] for a real workload. Benchmark [workload] against [baseline] and include [trade-off], not just the best-case number. If the result holds, builders working on [use case] may benefit first."
    ),
    "Funding & opportunities": (
        "Mechanism: verify eligibility, deadline, deliverable, reward conditions, and whether participation requires spending or risky permissions.",
        "Second order: explain what behavior the incentive is designed to attract and how to distinguish opportunity from farming noise.",
        "Builder lens: create a verified tracker of official links, dates, eligibility, and completion requirements.",
        "Before calling this an opportunity, verify [eligibility], [deadline], and [actual reward conditions] from the official source. The strategic question is what behavior the program rewards: [behavior]. It may suit [participant type], but [cost/constraint] changes the calculation."
    ),
    "Crypto research": (
        "Mechanism: find the concrete technical or product change beneath the broad claim.",
        "Second order: explain what this could change for a specific user group if the claim holds.",
        "Builder lens: test the claim with a small demo, public dataset, or reproducible comparison.",
        "The headline is [verified change]. The detail worth investigating is [mechanism or constraint], because it could change [specific outcome] for [user group]. Validate it with [evidence/test] before drawing a conclusion. The biggest unknown is [caveat]."
    ),
}

TOOL_IDEAS = [
    (("stablecoin", "payment", "remittance"), "Stablecoin route and fee comparator", "Compare transfer cost, settlement time and supported networks from public data."),
    (("security", "exploit", "vulnerability", "audit"), "Contract-change watchlist", "Track verified contract or repository changes and link each alert to its primary source."),
    (("github", "open source", "sdk", "api", "repository", "repo", "framework"), "Developer resource index", "Collect useful repositories with recent activity, a clear use case and setup instructions."),
    (("wallet", "onchain", "on-chain", "transaction", "contract"), "Readable transaction explainer", "Translate public transaction fields and contract calls into a traceable, human-readable walkthrough."),
    (("defi", "liquidity", "yield", "lending"), "Protocol metric comparison", "Compare selected public metrics across protocols while showing timestamps and source links."),
    (("ai", "agent", "automation"), "Agent integration starter kit", "Turn a documented API or agent framework into a small, reproducible working example."),
    (("hackathon", "grant", "funding", "airdrop", "incentive", "rewards"), "Opportunity verification tracker", "Track official eligibility, deadlines and source links, separating confirmed details from rumors."),
]

def _normal(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()

def _has_term(text, term):
    if term in {"ai", "l2", "api", "sdk", "rpc", "dex", "usdc", "usdt"}:
        return re.search(r"\b" + re.escape(term) + r"\b", text) is not None
    return term in text

def _topic(item):
    text = " " + _normal(item.get("text", "")).lower() + " "
    for topic, terms in TOPIC_RULES:
        if any(_has_term(text, term) for term in terms):
            return topic
    return "Crypto research"

def _score(item):
    text = _normal(item.get("text", "")).lower()
    source = str(item.get("source", "")).lower()
    score = 0
    if str(item.get("url", "")).startswith(("https://", "http://")):
        score += 2
    if source in {"github", "web", "x_high_performance"}:
        score += 1
    if any(word in text for word in ("how to", "guide", "tutorial", "open source", "sdk", "api", "research", "finding", "security", "release", "proposal", "data", "benchmark")):
        score += 3
    if any(word in text for word in ("new", "launch", "released", "today", "breaking", "vulnerability", "exploit", "proposal")):
        score += 2
    if len(text) >= 180:
        score += 1
    views = item.get("views", 0)
    if isinstance(views, (int, float)) and views >= 50000:
        score += 1
    return score

def _title(item):
    text = _normal(item.get("text", ""))
    sentence = re.split(r"(?<=[.!?])\s+", text, maxsplit=1)[0]
    return (sentence or text)[:170].rstrip()

def _tool_idea(item):
    text = _normal(item.get("text", "")).lower()
    for terms, name, description in TOOL_IDEAS:
        if any(_has_term(text, term) for term in terms):
            return name, description
    return "Evidence-linked topic tracker", "Collect primary sources and meaningful updates for this topic, with dates and duplicate detection."

def _editorial_angles(item):
    return ANGLE_PLAYBOOK.get(_topic(item), ANGLE_PLAYBOOK["Crypto research"])

def _research_prompt(item):
    topic = _topic(item)
    source = str(item.get("source", "unknown")).upper()
    url = str(item.get("url", "")).strip()
    views = item.get("views")
    details = f"Topic: {topic} | Source: {source}"
    if isinstance(views, (int, float)) and views > 0:
        details += f" | X views: {views:,}"
    mechanism, second_order, builder, draft = _editorial_angles(item)
    return (
        f"• {topic}: {_title(item)}\n"
        f"  Signal: {details}. Treat the source as a lead; verify the underlying claim.\n"
        f"  DIFFERENTIATION ANGLES\n"
        f"  1. {mechanism}\n"
        f"  2. {second_order}\n"
        f"  3. {builder}\n"
        f"  POST SCAFFOLD (fill with verified specifics)\n"
        f"  {draft}\n"
        f"  Source: {url}"
    )

def build_editorial_digest(items, limit=3):
    """Return a compact Telegram digest of ranked findings and differentiated writing guidance."""
    valid = [item for item in items or [] if isinstance(item, dict) and item.get("url") and item.get("text")]
    if not valid:
        return ""
    ranked = sorted(valid, key=lambda item: (_score(item), int(item.get("views") or 0)), reverse=True)
    chosen = ranked[:max(1, min(int(limit), 3))]
    sections = [
        "EDITORIAL INTELLIGENCE | HUMAN REVIEW REQUIRED",
        "",
        "Goal: publish what others can learn from you, not a rewrite of the headline. Angles are hypotheses; fill placeholders only after checking evidence.",
        "",
    ]
    sections.extend(_research_prompt(item) for item in chosen)
    idea_name, idea_desc = _tool_idea(chosen[0])
    sections.extend([
        "",
        "BUILD RADAR",
        f"Idea to validate: {idea_name}",
        idea_desc,
        "Before building: check alternatives and ask real users whether the problem matters.",
        "",
        "PUBLISHING RULE",
        "Use one specific fact, one defensible interpretation, one caveat, and one practical takeaway. Never present a hypothesis as a confirmed fact.",
    ])
    digest = "\n".join(sections)
    if len(digest) > 3900:
        return build_editorial_digest(chosen[:1], limit=1)
    return digest
