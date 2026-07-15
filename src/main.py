"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    from src.recommender import load_songs, recommend_songs
except ModuleNotFoundError:
    from recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Distinct example taste profiles to try
    profiles = {
        "High-Energy Pop": {"genre": "pop", "mood": "happy", "energy": 0.9},
        "Chill Lofi": {"genre": "lofi", "mood": "chill", "energy": 0.4},
        "Deep Intense Rock": {"genre": "rock", "mood": "intense", "energy": 0.85},
        # --- Adversarial / edge-case profiles ---------------------------------
        # Designed to probe whether the scoring logic can be "tricked" or
        # produces surprising rankings. See README "Adversarial Evaluation".
        #
        # 1. Genre they love vs. energy they want, pulling opposite directions:
        #    lofi is always low-energy, but they ask for max energy. Which wins?
        "Conflicting: Hyper Lofi": {"genre": "lofi", "mood": "sad", "energy": 0.95},
        # 2. A genre that isn't in the catalog at all -> genre bonus never fires;
        #    ranking must fall back to mood + energy gracefully.
        "Impossible Genre (kpop)": {"genre": "kpop", "mood": "happy", "energy": 0.7},
        # 3. Out-of-range energy (5.0). Energy points are 1.5*(1-|Δ|), so this
        #    goes deeply NEGATIVE -> the "best" song is just the least-penalized.
        "Out-of-Range Energy": {"genre": "pop", "mood": "happy", "energy": 5.0},
        # 4. Genre + mood + energy all describe different, incompatible vibes:
        #    they claim to love metal but want a chill, near-silent track.
        "Everything Conflicts": {"genre": "metal", "mood": "chill", "energy": 0.1},
        # 5. No usable signal: blank genre/mood, energy dead-center. Nothing can
        #    match on genre/mood, so ranking is pure energy + popularity tiebreak.
        "Blank / No Signal": {"genre": "", "mood": "", "energy": 0.5},
    }

    for name, user_prefs in profiles.items():
        recommendations = recommend_songs(user_prefs, songs, k=5)

        print("\n" + "=" * 44)
        print(f"  {name.upper()}")
        print("=" * 44)
        for rank, (song, score, explanation) in enumerate(recommendations, start=1):
            print(f"\n{rank}. {song['title']} - {song['artist']}   [score: {score:.2f}]")
            for reason in explanation.split(", "):
                print(f"     - {reason}")
        print()


if __name__ == "__main__":
    main()
