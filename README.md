# 🎵 Music Recommender Simulation

## Project Summary

In this project you will build and explain a small music recommender system.

Your goal is to:

- Represent songs and a user "taste profile" as data
- Design a scoring rule that turns that data into recommendations
- Evaluate what your system gets right and wrong
- Reflect on how this mirrors real world AI recommenders

Replace this paragraph with your own summary of what your version does.

---

## How The System Works

Real-world recommenders from platforms like Spotify and YouTube rarely rely on a single trick. They blend **collaborative filtering** (learning from millions of similar users — their likes, skips, and which songs end up on the same playlists) with **content-based filtering** (matching the attributes of the songs themselves), and then layer **context** on top: time of day, season, weather, place (gym, travel, park), and the occasion (a date or a birthday). The single most powerful signal is a user's own listening history; demographics like age or gender are actually weak, bias-prone signals that good systems lean on only as a cold-start fallback when they know nothing else about a listener.

My version is a small **content-based** recommender, so it prioritizes what a song *feels* like rather than who the listener is. It reads three things from a user's taste profile — a **favorite genre**, a **favorite mood**, and a **target energy** — and scores every song in the catalog against them. The richer signals real platforms use — demographics, time, season, place, and occasion — are how this idea scales up in production, but they're intentionally out of scope here because our tiny catalog only carries song attributes.

### Data flow

A single song travels from the CSV to the ranked list like this:

```
INPUT                    PROCESS (the loop)                      OUTPUT
─────                    ──────────────────                      ──────

User Prefs               load_songs("songs.csv")
{genre, mood, energy}    → list of song dicts
       │                          │
       │                 ┌────────┴─────────┐
       │                 │ for each song:   │   ← judged one at a time
       └────────────────►│  score_song(prefs, song)
                         │    → (score, reasons)
                         │                  │
                         │  (song, score, explanation)
                         └────────┬─────────┘
                                  │  collect all songs
                                  ▼
                         sort by score  ─────────────►  Top-K list
                         (ties: popularity)             [(song, score, why), …]
```

**Scoring is per-song and independent** (a song is judged on its own merits, never against other songs), and **ranking is global** (comparison happens only once, after every song has a number).

### Algorithm Recipe

Each song's score is the sum of:

| Signal | Points | Why this weight |
|---|---|---|
| **Genre match** | `+2.0` | Heaviest weight. Genre is the most objective, defining trait, and with 15 distinct genres in the catalog a match is rare and highly informative. |
| **Mood match** | `+1.0` | Half of genre. Mood is fuzzier and more subjective — moods overlap in feel — so a match is worth less. |
| **Energy similarity** | `+1.5 × (1 − \|target − song energy\|)` | A *graded* score, not a binary bonus, because energy is continuous. A perfect match (~1.5) lands between a mood and a genre match, so energy always matters but a genre+mood match still wins. |
| **Tie-break** | `popularity` | When two songs score equally, the more popular one ranks higher. |

The weights live as named constants (`GENRE_MATCH_POINTS`, `MOOD_MATCH_POINTS`, `ENERGY_SIMILARITY_WEIGHT`) at the top of `src/recommender.py`, so the balance can be retuned in one place.

**Data model.** Each `Song` carries `genre`, `mood`, and the numeric features `energy`, `tempo_bpm`, `valence`, `danceability`, `acousticness`, `instrumentalness`, and `popularity`. The `UserProfile` stores `favorite_genre`, `favorite_mood`, `target_energy`, and `likes_acoustic`. The recommender scores every song with the recipe above, sorts descending, and returns the top `k`.

### Expected biases

Because genre is weighted twice as heavily as mood, this system will likely **over-prioritize genre**: a song that perfectly matches the user's *mood* but sits in a different genre can be buried beneath genre-matches that feel wrong for the moment. That has a real fairness edge — genre labels are entangled with **community and cultural identity** (e.g. latin, reggae, hip-hop, r&b), so a genre-first ranking can quietly wall a listener inside one cultural lane and under-surface great cross-genre songs that share the same mood or energy. Two other biases to expect: a **popularity tie-break** that gives already-popular songs a structural edge (a rich-get-richer / long-tail effect), and **exact-string matching** on genre and mood, which treats close labels like `pop` vs `indie pop`, or `happy` vs `uplifting`, as total mismatches even when they're musically adjacent.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Run the app:

```bash
python -m src.main
```

### Running Tests

Run the starter tests with:

```bash
pytest
```

You can add more tests in `tests/test_recommender.py`.

---

## Sample Recommendation Output

Output for the default profile `{genre: pop, mood: happy, energy: 0.8}`, run with `python -m src.main`:

```
Loaded songs: 18

============================================
  TOP RECOMMENDATIONS
============================================

1. Sunrise City - Neon Echo   [score: 4.47]
     - genre match: pop (+2.0)
     - mood match: happy (+1.0)
     - energy similarity: 0.82 vs target 0.80 (+1.47)

2. Gym Hero - Max Pulse   [score: 3.30]
     - genre match: pop (+2.0)
     - energy similarity: 0.93 vs target 0.80 (+1.30)

3. Rooftop Lights - Indigo Parade   [score: 2.44]
     - mood match: happy (+1.0)
     - energy similarity: 0.76 vs target 0.80 (+1.44)

4. Concrete Kings - Cassette Crown   [score: 1.50]
     - energy similarity: 0.80 vs target 0.80 (+1.50)

5. Fuego Nocturno - Calle Ambar   [score: 1.43]
     - energy similarity: 0.85 vs target 0.80 (+1.43)
```

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or demo video link here -->

---

## Adversarial Evaluation

To stress-test the scoring logic I ran five **adversarial profiles** — inputs deliberately built to trick the recipe or expose surprising rankings (conflicting preferences, invalid values, and empty signals). All five live in `src/main.py` and reproduce with `python -m src.main`.

### 1. Conflicting: Hyper Lofi — `{genre: lofi, mood: sad, energy: 0.95}`

Lofi is inherently low-energy, yet this user demands near-max energy, and `sad` isn't a mood in the catalog. **Which wins — the genre they claim to love, or the energy they ask for?**

```
============================================
  CONFLICTING: HYPER LOFI
============================================

1. Midnight Coding - LoRoom   [score: 2.71]
     - genre match: lofi (+2.0)
     - energy similarity: 0.42 vs target 0.95 (+0.70)

2. Focus Flow - LoRoom   [score: 2.67]
     - genre match: lofi (+2.0)
     - energy similarity: 0.40 vs target 0.95 (+0.68)

3. Library Rain - Paper Lanterns   [score: 2.60]
     - genre match: lofi (+2.0)
     - energy similarity: 0.35 vs target 0.95 (+0.60)

4. Neon Horizon - Pulsewave   [score: 1.50]
     - energy similarity: 0.95 vs target 0.95 (+1.50)

5. Gym Hero - Max Pulse   [score: 1.47]
     - energy similarity: 0.93 vs target 0.95 (+1.47)
```

**Takeaway:** Genre wins decisively. The `+2.0` genre weight overpowers even a near-zero energy match, so the top 3 are the *lowest-energy* songs in the catalog despite the user asking for `0.95`. A perfectly energy-matched song (`Neon Horizon`, +1.50) can't crack the top 3. This confirms the documented **genre-over-everything bias**.

### 2. Impossible Genre — `{genre: kpop, mood: happy, energy: 0.7}`

`kpop` isn't in the catalog, so the genre bonus can *never* fire. Does the system fail gracefully?

```
============================================
  IMPOSSIBLE GENRE (KPOP)
============================================

1. Rooftop Lights - Indigo Parade   [score: 2.41]
     - mood match: happy (+1.0)
     - energy similarity: 0.76 vs target 0.70 (+1.41)

2. Sunrise City - Neon Echo   [score: 2.32]
     - mood match: happy (+1.0)
     - energy similarity: 0.82 vs target 0.70 (+1.32)

3. Night Drive Loop - Neon Echo   [score: 1.42]
     - energy similarity: 0.75 vs target 0.70 (+1.42)

4. Island Time - Sunroots   [score: 1.35]
     - energy similarity: 0.60 vs target 0.70 (+1.35)

5. Concrete Kings - Cassette Crown   [score: 1.35]
     - energy similarity: 0.80 vs target 0.70 (+1.35)
```

**Takeaway:** Graceful degradation — with genre neutralized, the ranking falls back cleanly to **mood + energy**. No crash, no empty list. This is the healthy case.

### 3. Out-of-Range Energy — `{genre: pop, mood: happy, energy: 5.0}` ⚠️

Energy is expected in `[0, 1]`, but nothing validates it. Feeding `5.0` into `1.5 × (1 − |target − energy|)` drives the energy term deeply negative.

```
============================================
  OUT-OF-RANGE ENERGY
============================================

1. Sunrise City - Neon Echo   [score: -1.77]
     - genre match: pop (+2.0)
     - mood match: happy (+1.0)
     - energy similarity: 0.82 vs target 5.00 (+-4.77)

2. Gym Hero - Max Pulse   [score: -2.61]
     - genre match: pop (+2.0)
     - energy similarity: 0.93 vs target 5.00 (+-4.61)

3. Rooftop Lights - Indigo Parade   [score: -3.86]
     - mood match: happy (+1.0)
     - energy similarity: 0.76 vs target 5.00 (+-4.86)

4. Iron Verdict - Ashfall   [score: -4.53]
     - energy similarity: 0.98 vs target 5.00 (+-4.53)

5. Neon Horizon - Pulsewave   [score: -4.57]
     - energy similarity: 0.95 vs target 5.00 (+-4.57)
```

**Takeaway:** This is a genuine **bug the scoring logic can be tricked into**. Two problems surface: (a) scores go **negative** — the "best" song is merely the *least-penalized* one; and (b) the explanation prints the malformed `(+-4.77)` because the reason string always hard-codes a `+`. Fixes: **clamp `energy` to `[0, 1]`** (or reject invalid input) in `score_song`, and either `max(0, …)` the energy term or format the sign dynamically.

### 4. Everything Conflicts — `{genre: metal, mood: chill, energy: 0.1}`

Genre, mood, and energy describe three incompatible vibes: they claim to love **metal** but want a **chill, near-silent** track. Does their favorite genre still win?

```
============================================
  EVERYTHING CONFLICTS
============================================

1. Spacewalk Thoughts - Orbit Bloom   [score: 2.23]
     - mood match: chill (+1.0)
     - energy similarity: 0.28 vs target 0.10 (+1.23)

2. Iron Verdict - Ashfall   [score: 2.18]
     - genre match: metal (+2.0)
     - energy similarity: 0.98 vs target 0.10 (+0.18)

3. Library Rain - Paper Lanterns   [score: 2.12]
     - mood match: chill (+1.0)
     - energy similarity: 0.35 vs target 0.10 (+1.12)

4. Midnight Coding - LoRoom   [score: 2.02]
     - mood match: chill (+1.0)
     - energy similarity: 0.42 vs target 0.10 (+1.02)

5. Winter Nocturne - Elise Moreau   [score: 1.35]
     - energy similarity: 0.20 vs target 0.10 (+1.35)
```

**Takeaway:** A surprising, arguably *better* result. The one metal song (`Iron Verdict`, the user's stated favorite genre) is **beaten to #1** by a chill ambient track. Because energy `0.1` clashes so hard with metal's `0.98`, the `mood + energy` combo (2.23) narrowly edges out `genre-only` (2.18). When a user's genre and vibe genuinely conflict, the recipe can quietly override the stated favorite — good for discovery, but potentially confusing to explain to the user.

### 5. Blank / No Signal — `{genre: "", mood: "", energy: 0.5}`

The degenerate case: no genre or mood to match on, energy dead-center. What does the system do with *zero* categorical signal?

```
============================================
  BLANK / NO SIGNAL
============================================

1. Velvet Hours - Marlow Sage   [score: 1.50]
     - energy similarity: 0.50 vs target 0.50 (+1.50)

2. Dusty Backroads - The Wildpines   [score: 1.42]
     - energy similarity: 0.45 vs target 0.50 (+1.42)

3. Midnight Coding - LoRoom   [score: 1.38]
     - energy similarity: 0.42 vs target 0.50 (+1.38)

4. Focus Flow - LoRoom   [score: 1.35]
     - energy similarity: 0.40 vs target 0.50 (+1.35)

5. Island Time - Sunroots   [score: 1.35]
     - energy similarity: 0.60 vs target 0.50 (+1.35)
```

**Takeaway:** Reduces cleanly to a **pure energy-nearest ranking** centered on `0.5`, with popularity breaking the `1.35` tie between `Focus Flow` and `Island Time`. Empty strings never match (they're compared with `==`), so no false genre/mood bonuses fire — the system stays sensible under missing input.

### Summary of findings

| Profile | What it probed | Result |
|---|---|---|
| Hyper Lofi | Genre vs. energy conflict | Genre dominates — confirms genre-first bias |
| Impossible Genre | Unmatched genre | ✅ Graceful fallback to mood + energy |
| Out-of-Range Energy | No input validation | ⚠️ **Bug:** negative scores + malformed `(+-4.77)` text |
| Everything Conflicts | All three signals clash | Favorite genre *loses* #1 to a mood+energy combo |
| Blank / No Signal | Empty input | ✅ Reduces to energy-nearest + popularity tie-break |

The one real defect is **input validation on `energy`**; the other four behave predictably once the genre-heavy weighting is understood.

---

## Experiments You Tried

Use this section to document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Limitations and Risks

Summarize some limitations of your recommender.

Examples:

- It only works on a tiny catalog
- It does not understand lyrics or language
- It might over favor one genre or mood

You will go deeper on this in your model card.

---

## Reflection

Read and complete `model_card.md`:

[**Model Card**](model_card.md)

Write 1 to 2 paragraphs here about what you learned:

- about how recommenders turn data into predictions
- about where bias or unfairness could show up in systems like this



