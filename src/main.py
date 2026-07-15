"""
Command line runner for the Music Recommender Simulation.

Demonstrates the four challenge features:
  1. Advanced song attributes (era, mood tags, language, explicit, length)
  2. Multiple scoring modes  (balanced / genre_first / mood_first / energy_focused)
  3. A diversity penalty      (no single artist/genre floods the top results)
  4. A formatted results table (tabulate, with an ASCII fallback)
"""

try:
    from src.recommender import load_songs, recommend_songs, SCORING_MODES
except ModuleNotFoundError:
    from recommender import load_songs, recommend_songs, SCORING_MODES


def format_table(recommendations) -> str:
    """Render the (song, score, explanation) tuples as a readable table."""
    headers = ["#", "Title", "Artist", "Genre", "Score", "Why it was picked"]
    rows = []
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        rows.append([rank, song["title"], song["artist"], song["genre"], f"{score:.2f}", explanation])

    try:
        from tabulate import tabulate
        return tabulate(rows, headers=headers, tablefmt="grid")
    except ImportError:
        # Simple ASCII fallback so the app still runs without tabulate installed.
        lines = []
        for r in rows:
            lines.append(f"{r[0]}. {r[1]} - {r[2]}  [{r[3]}]  score {r[4]}")
            for reason in r[5].split(", "):
                lines.append(f"     - {reason}")
        return "\n".join(lines)


def show(title: str, recommendations) -> None:
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print(format_table(recommendations))


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Profiles exercise the new advanced attributes: era, language, length,
    # explicit avoidance, and secondary vibe tags.
    profiles = {
        "High-Energy Pop": {"genre": "pop", "mood": "happy", "energy": 0.9, "decade": 2020},
        "Chill Lofi Study": {"genre": "lofi", "mood": "chill", "energy": 0.4,
                              "language": "instrumental", "length": "short"},
        "Clean Latin Night": {"genre": "latin", "mood": "passionate", "energy": 0.85,
                              "language": "spanish", "avoid_explicit": True, "mood_tag": "sensual"},
    }

    # --- Balanced mode + diversity penalty (Challenges 1, 3, 4) --------------
    print("\n\n#### BALANCED MODE  (with diversity penalty) ####")
    for name, prefs in profiles.items():
        recs = recommend_songs(prefs, songs, k=5, mode="balanced",
                               artist_penalty=1.5, genre_penalty=0.75)
        show(name, recs)

    # --- Same profile across every scoring mode (Challenge 2) ----------------
    print("\n\n#### SCORING MODES  (High-Energy Pop across strategies) ####")
    demo = {"genre": "pop", "mood": "happy", "energy": 0.9}
    for mode in SCORING_MODES:
        recs = recommend_songs(demo, songs, k=5, mode=mode)
        show(f"MODE: {mode}", recs)


if __name__ == "__main__":
    main()
