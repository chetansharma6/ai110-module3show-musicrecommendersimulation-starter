# AI Interactions Log

> **Stretch features only.** Documents the AI-assisted work on the four stretch challenges.

---

## Agentic Workflow (SF8)

> Document your experience using an AI agent (e.g., Cursor Agent, Claude, Copilot) to make multi-step changes autonomously.

**What task did you give the agent?**

Challenge 1 — add 5+ advanced song attributes to the dataset and make the scoring
logic actually use them, without breaking the existing tests or the baseline
recipe.

**Prompts used:**

- "Add 5 or more complex attributes to `data/songs.csv` that aren't in the
  baseline (e.g. release decade, detailed mood tags, language, explicit flag,
  duration). Update the scoring in `src/recommender.py` so these attributes
  affect the score. Keep the existing tests passing."
- "Make the new preferences optional so the old profiles and the `Song`/
  `UserProfile` dataclasses still work with defaults."

**What did the agent generate or change?**

- `data/songs.csv`: added 5 new columns to all 18 rows — `release_decade`,
  `mood_tags` (`;`-separated), `language`, `explicit` (0/1), `duration_sec`.
- `src/recommender.py`:
  - New default fields on the `Song` dataclass (all with defaults) and optional
    fields on `UserProfile` (`preferred_decade`, `preferred_language`,
    `avoid_explicit`).
  - New weight constants (`DECADE_MATCH_POINTS`, `MOOD_TAG_POINTS`,
    `LANGUAGE_MATCH_POINTS`, `EXPLICIT_PENALTY`, `LENGTH_MATCH_POINTS`).
  - `score_song` extended: era match, secondary vibe-tag match, language match,
    explicit penalty, and a track-length preference — each applied only when the
    matching preference is present.
  - Updated `load_songs` to parse the new integer columns.

**What did you verify or fix manually?**

- Ran `pytest` — the two starter tests still pass because every new field has a
  default, so `Song(...)` calls in the tests are unchanged.
- Ran `python -m src.main` and confirmed the new reasons actually appear:
  "era match: 2020s (+0.75)", "language match: instrumental (+0.50)",
  "vibe tag match: 'sensual' (+0.50)", "length fits 'short' (+0.50)".
- Caught and fixed a display bug the AI reproduced from the original code: a
  negative energy value printed as `(+-4.77)`. Added a `_signed()` helper so
  penalties render as `-1.00` instead of `+-1.00`.

---

## Design Pattern (SF10)

> Document how AI helped you choose or implement a design pattern.

**Which design pattern did you use?**

A lightweight **Strategy pattern** for Challenge 2 (multiple scoring modes).

**How did AI help you brainstorm or implement it?**

I asked the AI how to let a user switch ranking strategies (genre-first,
mood-first, energy-focused) without duplicating the scoring code. It compared a
few options:

- **if/elif branches per mode** — simple but the scoring math gets copy-pasted
  and drifts out of sync.
- **A subclass per strategy** — classic Strategy, but heavy for three numbers.
- **A weight table (chosen)** — one scoring algorithm, and each "strategy" is
  just a named set of weights it looks up. This keeps the algorithm in one place
  and makes adding a new mode a one-line change.

We went with the weight-table version because it is the smallest change that
still cleanly separates *policy* (the weights) from *mechanism* (the scoring
loop).

**How does the pattern appear in your final code?**

- `SCORING_MODES` in `src/recommender.py` is the strategy registry:
  `{"balanced": {...}, "genre_first": {...}, "mood_first": {...},
  "energy_focused": {...}}`.
- `score_song(user_prefs, song, mode="balanced")` and `Recommender._score(...)`
  look up `SCORING_MODES[mode]` and apply those weights. `balanced` reproduces
  the original recipe exactly, so nothing else had to change.
- `src/main.py` loops over `SCORING_MODES` to show the same profile ranked under
  every strategy.

---

## Diversity & Fairness Rule (SF — Challenge 3)

**The rule:** when building the top-K list, songs are chosen one at a time
(greedy). Each time a song is picked, its artist and genre are remembered. Any
remaining candidate is then docked points before the next pick:

```
adjusted_score = base_score
                 - artist_penalty * (times this artist already chosen)
                 - genre_penalty  * (times this genre already chosen)
```

So the *first* song by an artist keeps its full score, the *second* loses
`artist_penalty`, the third loses `2 * artist_penalty`, and so on. This stops one
artist or genre from flooding the results. It lives in `recommend_songs(...)`
(params `artist_penalty`, `genre_penalty`); with both at 0 the original
sort-by-score behavior is preserved. In the demo run `Gym Hero` was docked
-0.75 (same genre as the #1 pop song) and a third lofi track, `Focus Flow`, was
docked -3.00.

---

## Readable Table Output (SF — Challenge 4)

The terminal output uses the **`tabulate`** library (`tablefmt="grid"`) to print
each profile's recommendations as a bordered table with columns *#, Title,
Artist, Genre, Score,* and *Why it was picked* (the full reason string). If
`tabulate` isn't installed, `format_table()` in `src/main.py` falls back to a
plain ASCII list so the app still runs. `tabulate` was added to
`requirements.txt`.
