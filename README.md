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



