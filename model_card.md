# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

**VibeFinder 1.0**

A small tool that finds songs to match your vibe.

---

## 2. Goal / Task  

VibeFinder suggests songs. You tell it what you like. It gives you the top 5 matches.

- You give it a favorite genre, a favorite mood, and a target energy level.
- It picks songs from the catalog that fit those three things best.
- It also tells you *why* each song was picked.
- This is a classroom project for learning, not a real app for real users.

---

## 3. Algorithm Summary  

The model gives each song points, then ranks them. Highest score wins.

- **Genre match:** +2 points. This matters most.
- **Mood match:** +1 point. This matters half as much.
- **Energy match:** up to +1.5 points. The closer the song's energy is to your target, the more points it gets.
- **Tie-breaker:** if two songs tie, the more popular one wins.

It adds up the points for every song, sorts them, and shows the top 5. It also lists the reasons for each pick so the choice is easy to understand.

---

## 4. Data Used  

The catalog is small and lives in one file (`data/songs.csv`).

- **Size:** 18 songs.
- **Genres:** 15 different ones, like pop, lofi, rock, jazz, hip-hop, edm, metal, and latin.
- **Moods:** happy, chill, intense, focused, romantic, and more.
- **Features per song:** genre, mood, energy, tempo, valence, danceability, acousticness, instrumentalness, and popularity.
- **Limits:** the catalog is tiny, so many real tastes are missing. Some genres have only one song. It has no lyrics, no language info, and no real listening history.

---

## 5. Strengths  

The model works well for clear, simple tastes.

- It gives good picks when a user's genre, mood, and energy all point the same way (like a high-energy pop fan).
- It handles missing info gracefully. A genre that isn't in the catalog doesn't crash it — it just uses mood and energy instead.
- Every pick comes with a plain reason, so it's easy to see why a song was chosen.
- It matched our intuition on the three main test profiles.

---

## 6. Limitations and Bias 

Where the system struggles or behaves unfairly. 

**Genre-first filter bubble.** The biggest weakness we found is that the scoring is structurally *genre-first*: a genre match is worth `+2.0`, but even a **perfect** energy match caps out at `+1.5`, so a genre match can never be beaten by vibe alone. In the "Hyper Lofi" experiment (`genre: lofi, energy: 0.95`) the system returned the three *lowest*-energy songs in the catalog simply because they were lofi, completely ignoring the user's explicit demand for high energy. This means a listener whose real preference is a *feeling* (energy/mood) rather than a genre label gets walled into their stated genre — a filter bubble made worse by exact-string matching, which treats musically adjacent labels like `pop` vs `indie pop` as total mismatches. The "energy gap" term also has no input validation: an out-of-range energy like `5.0` produced **negative scores** and a malformed `(+-4.77)` explanation, showing the energy math can silently break. Finally, the popularity tie-break gives already-popular songs a structural edge, a rich-get-richer effect that quietly buries lesser-known tracks.

---

## 7. Evaluation  

How you checked whether the recommender behaved as expected.

**Profiles tested.** We ran three realistic profiles — **High-Energy Pop** (`pop, happy, 0.9`), **Chill Lofi** (`lofi, chill, 0.4`), **Deep Intense Rock** (`rock, intense, 0.85`) — plus five adversarial profiles built to trick the logic: **Hyper Lofi** (`lofi, sad, 0.95`), **Impossible Genre** (`kpop, happy, 0.7`), **Out-of-Range Energy** (`pop, happy, 5.0`), **Everything Conflicts** (`metal, chill, 0.1`), and **Blank / No Signal** (`"", "", 0.5`). We looked at whether the top-5 matched intuition and how each preference field moved the ranking.

**What surprised us.** Two things. First, in *Everything Conflicts* the user's stated favorite genre (metal, +2.0) actually **lost the #1 slot** to a chill ambient track, because its energy clashed so badly (`0.98` vs target `0.1`) that mood+energy edged out genre-only — the "favorite" can be silently overridden. Second, *Out-of-Range Energy* wasn't rejected at all: it produced negative scores and broken explanation text, revealing there's no input validation.

**Pairwise comparisons.**

- **High-Energy Pop vs. Chill Lofi:** Opposite ends of the energy axis. Pop pulls up-tempo tracks like *Sunrise City* (energy 0.82); Lofi shifts to quiet study tracks like *Midnight Coding* (0.42). Makes sense — same recipe, but the target-energy pole flips the whole list.
- **High-Energy Pop vs. Deep Intense Rock:** Both want high energy, so their pools overlap (*Gym Hero* appears in both), but the genre bonus separates them — Pop crowns a pop song, Rock crowns *Storm Runner*. This shows genre, not energy, is the tiebreaker between two high-energy users.
- **Chill Lofi vs. Deep Intense Rock:** A near-total inversion: low-energy chill vs. high-energy intense, and no song appears in both top-5s. Confirms the model cleanly separates users at opposite energy+genre extremes — the "healthy" case.
- **Chill Lofi vs. Hyper Lofi:** Same genre, opposite energy (`0.4` vs `0.95`). Surprisingly the **top 3 barely change** — both are lofi songs — because the `+2.0` genre bonus swamps the energy difference. This pair best demonstrates the genre-first filter bubble: the energy field is almost cosmetic once genre matches.
- **High-Energy Pop vs. Impossible Genre:** Identical mood/energy region, but `kpop` matches nothing, so the genre bonus never fires and ranking falls back to mood+energy. *Rooftop Lights* rises because mood alone now decides — a clean look at how the system degrades when genre is unavailable.
- **Impossible Genre vs. Blank / No Signal:** Impossible Genre still has a valid mood (`happy`) to lean on; Blank has neither genre nor mood, so it collapses to a pure energy-nearest ranking around `0.5` with popularity breaking ties. The comparison isolates exactly how much a single mood match is worth (`+1.0`) versus no categorical signal at all.
- **High-Energy Pop vs. Out-of-Range Energy:** Same genre and mood, but energy `0.9` → `5.0` flips every score **negative** and the "best" song becomes the least-penalized rather than the best-matched. This pair proves the energy term needs clamping to `[0, 1]`.

No numeric metrics — evaluation was by inspecting and comparing top-5 lists against intuition.

---

## 8. Intended Use and Non-Intended Use  

**Intended use:**

- Learning how a recommender turns data into picks.
- Trying out different user tastes and seeing how the list changes.
- Classroom experiments and demos.

**Not intended use:**

- Real music apps or real users.
- Any real decision that affects a person.
- Judging an artist's or a genre's worth. The scores only reflect our simple rules, not real quality.

---

## 9. Ideas for Improvement  

Three things we'd change next:

- **Validate the input.** Keep energy between 0 and 1 so bad values can't break the scores.
- **Loosen the matching.** Treat close labels like `pop` and `indie pop` as partial matches, not total misses.
- **Add variety.** Mix up the top 5 so a user isn't stuck in one genre. This would soften the genre-first filter bubble we found.

---

## 10. Personal Reflection  

My biggest learning moment was watching the "Everything Conflicts" test. I told the system metal was my favorite genre, but a quiet ambient song still won the top spot. At first I thought it was a bug. Then I did the math and saw the mood and energy points had simply added up to more than the genre bonus. That was the moment recommendations stopped feeling like magic and started feeling like arithmetic.

AI tools sped me up a lot. They helped me draft the scoring rules, build weird test profiles, and write these notes. But I learned not to trust them blindly. The out-of-range energy test is a good example — the code happily accepted an energy of 5.0 and printed a broken "+-4.77" score. Nothing warned me. I only caught it because I actually read the output line by line. So the AI was great for speed, but I still had to be the one checking whether the results made sense.

What surprised me most was how something this simple could still feel like a real recommender. There's no machine learning here. It's just adding up points and sorting a list. But when the reasons print out next to each song, it *feels* like the app "gets" you. That taught me that a lot of what makes a recommendation feel smart is really just clear rules and a good explanation.

If I kept going, I'd first fix the input checks so bad numbers can't break the math. Then I'd make the matching less strict, so "pop" and "indie pop" count as close instead of totally different. And I'd add some variety to the top 5 so a listener isn't trapped in one genre. Mostly, though, this project made me want to look at my own music apps and ask what quiet little rules are deciding what I hear.
