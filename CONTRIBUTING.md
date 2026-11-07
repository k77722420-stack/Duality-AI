# Contributing to Duality AI

**Everybody is welcome here.**

The Duality AI is an open concept, published openly by its author so that
anyone who finds the idea interesting can build on it. If the two-hemisphere
design, the weighing hub, or the morality gate with leniency within reason
sparks something in you — a better mechanism, a sharper critique, a clause
the library is missing — you are invited to contribute it. Ideas grow when
people add to them.

*Concept by Kenneth Lee Blum Jr (November 2026), released under the
[MIT License](LICENSE).*

## How to contribute

- **Discuss first, if you like.** Open an issue to talk through an idea,
  raise a question about the design, or point out a weakness. Honest
  criticism is a contribution too — the thesis itself lists its open
  questions in Section 7, and they are genuine invitations.
- **Fork and send a pull request.** Fork the repository, make your change
  on your fork, and submit a pull request explaining what you changed and
  why. Small, clear pull requests are easier to review than large ones.
- **Improve the clause library.** The morality clauses live in
  [`config/morality_clauses.json`](config/morality_clauses.json) as data.
  Proposed clauses, clearer wording, and better leniency conditions are
  welcome by pull request — state your reasoning in the request, because
  the library *is* the moral standard of the design, and changes to it
  should be argued, not slipped in.

## Ground rules

These keep contributions faithful to what the Duality AI is:

1. **Keep the five-stage architecture intact as the core.** Base layer,
   logical hemisphere, creative hemisphere, hub, morality gate — build on
   the flow, extend it, implement it better, but do not quietly replace it
   with a different design under the same name. If you want to explore a
   different architecture, fork it and say so proudly.
2. **Respect the honesty rule.** No contribution may claim that the system
   is conscious, aware, or genuinely understands morality — the concept
   itself denies all three, in writing, in its thesis and disclaimer.
   Exaggerated claims about what this design does will not be merged.
   Precision is this project's house style.
3. **Keep the clause library as data.** Clauses must remain inspectable
   records in the JSON library, never buried in code, so that the standard
   in force can always be read.
4. **Examples must be labeled as examples.** Illustrations of the flow are
   welcome; presenting an illustration as evidence the design works is
   not.

## A note on tone

Contributors are expected to be decent to one another: argue with ideas,
not with people. The author built this concept in the open because he
believes scrutiny makes ideas stronger. Bring that spirit, and whatever
you build here is welcome.

Thank you for being part of it.
