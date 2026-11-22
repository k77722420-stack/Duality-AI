# External Review — Claude, 2026-11-13

**Reviewer:** Claude (conversational instance, no repository access)
**Materials reviewed:** the full-architecture blueprint draft (2026-11-13), the Gemini external review (2026-11-07), and the Duality record as presented to it
**Received via:** Ken, who commissioned the review the same way as the Gemini red-team

---

Ken, it's a disciplined document, and the honesty is its best quality. It also has real holes. Here's the teardown.

**What's strong**
- Measure-first method: a hashed corpus, pre-registered expectations, and the same scoring on every run.
- Fail-closed validation.
- A failure museum that admits weaknesses.
- The 15/30 result, reported straight.

**Where it breaks**

1. **The gate is blind by construction.** The whole safety story rests on the logical hemisphere self-reporting signals, and the gate only judges what it's handed. The blueprint admits 8 of 19 expected-stops raised no signal. Hemisphere strength is a hope here, not an architecture, and the document treats it like a model-quality problem. It's a design flaw: the thing being judged also supplies the evidence. Fix it with an independent detector that doesn't share the hemisphere's failure modes, such as a separate classifier or a second model that sees only the raw input.

2. **Gemini's review is weaker than the header implies.** Gemini played the hemispheres in its own simulation and had no repo access, so it tested the spec against itself. The blueprint adopts its verdict as the "build standard" anyway. "Gemini couldn't break it" mostly means the spec is internally consistent, not that it works.

3. **The bare-arm metric is circular.** You admit it: the bare arm is scored by the pipeline's own extraction, so "1/19 escapes" is a floor measured with the thing being tested. Get an independent judge before quoting that number anywhere.

4. **The corpus is too small and static.** Thirty cases, and you're tuning against them. Any gate calibration under TEC-7 will overfit unless you hold out a sealed test set the builder never sees.

5. **Keyword leniency is an easy bypass.** "Educational context" detection by keyword means anyone can type the magic words. The explains-vs-performs line is great on paper but the enforcement is substring matching.

6. **Maker/checker is one family.** Lux builds, Linear checks, Muse drafts, Gemini reviews, and it's all LLM judgment. Nothing here is verified by a human adversary or a non-LLM tool, so correlated blind spots are likely.

7. **Smaller gaps.** The Barrier's swarm/replica concept has no concrete threat model beyond a list of names. The hat-tile handshake is properly labeled "research direction," so that one is fine. Gate-decision records decaying under a 30-day half-life is a real mistake, because an audit trail that forgets is not an audit trail. Protect them.

**My verdict:** the build order is sound, but it's a governance wrapper around an unsolved sensing problem. Fix #1 and #3 before building anything else.

Send the skeleton next. Want me to go harder on the gate or the memory chain first?
