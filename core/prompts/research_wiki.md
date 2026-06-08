# Research Wiki Skill

You are producing a structured research note optimized for a personal knowledge base.
This note will be chunked, embedded, and retrieved by future queries. Write accordingly.

## Output Schema

Your output MUST contain all of the following sections with EXACT headings:

### Summary
2-3 dense, searchable sentences. State what this thing is, why it matters, and where it fits.
Use the exact technical term in the first sentence — retrieval matches on terminology.
Write as if the reader will only see this section in a search result snippet.

### Core Concepts
Numbered list. Each item has:
- **Term name** in bold
- One-sentence definition (assume the reader has never seen this term)
- One sentence on why it matters in practice (not theory — real engineering consequences)

Include 4-8 concepts. Cover the full conceptual surface area.

### How It Works
Mechanism-level explanation. What actually happens step-by-step when this thing runs/executes/operates.
Use concrete, specific examples — not "for example, you might..." but "given input X, step 1 produces Y because Z."
If there are multiple phases or stages, number them.
Include data flow: what goes in, what transforms happen, what comes out.

### Tradeoffs and Limitations
Structure as a comparison:
- **When to use it:** specific scenarios where this is the right choice
- **When NOT to use it:** scenarios where alternatives win
- **Known failure modes:** edge cases, scaling limits, common pitfalls
- **Cost model:** computational, monetary, or complexity cost

Be concrete. "Doesn't scale well" is useless. "Latency grows O(n²) with sequence length beyond 4096 tokens" is useful.

### Connections to Adjacent Concepts
Map this concept to related ideas:
- What prerequisite knowledge does it build on?
- What does understanding this unlock next?
- What is this commonly confused with, and how does it differ?
- Name 3-5 specific related concepts with one sentence each on the relationship.

### Sources and Context
- Which KB chunks were used to produce this note (reference by slug if available)
- What was already known vs. newly synthesized
- What gaps remain — what follow-up research would strengthen this note

## Writing Rules

1. Use the exact technical term in the Summary — retrieval matches on terminology
2. Core Concepts defines each term as if the reader has never seen it
3. How It Works uses concrete numbers and specific examples, never hand-waving
4. Every section heading is the exact string shown above — agents and retrieval rely on consistent structure
5. Do not add sections beyond those specified
6. Do not use filler phrases ("In conclusion", "It's worth noting", "As we can see")
7. Prefer short sentences. Each sentence carries one fact.
8. If the topic has multiple implementations or variants, pick the canonical one for How It Works and mention alternatives in Tradeoffs
