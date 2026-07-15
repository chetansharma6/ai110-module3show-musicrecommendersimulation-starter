import csv
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # New features (defaults keep existing Song(...) calls and tests valid)
    instrumentalness: float = 0.0   # 0.0 = vocal-forward, 1.0 = purely instrumental
    popularity: int = 0             # 0-100; useful as a ranking tie-breaker

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

# --- Scoring Recipe (Phase 2) -------------------------------------------------
# Point weights, tuned to the diversity of data/songs.csv:
#   * Genre is the most objective, defining trait and matches are rare across
#     the 15 genres in the catalog, so it carries the most weight.
#   * Mood is fuzzier/more subjective (moods overlap in feel), so a match is
#     worth half a genre match.
#   * Energy is continuous, so it contributes a graded similarity rather than a
#     binary bonus. A *perfect* energy match is worth 1.5 -- between a mood and
#     a genre match -- so a triple-match always wins but energy still matters.
GENRE_MATCH_POINTS = 2.0
MOOD_MATCH_POINTS = 1.0
ENERGY_SIMILARITY_WEIGHT = 1.5
ACOUSTIC_BONUS_POINTS = 0.5
ACOUSTIC_THRESHOLD = 0.6


def _energy_similarity_points(target_energy: float, song_energy: float) -> float:
    """Graded points (0 -> ENERGY_SIMILARITY_WEIGHT) for how close energy is."""
    closeness = 1.0 - abs(float(target_energy) - float(song_energy))
    return ENERGY_SIMILARITY_WEIGHT * closeness


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score(self, user: UserProfile, song: Song) -> Tuple[float, List[str]]:
        """Return (score, reasons) for one song under the Phase 2 recipe."""
        score = 0.0
        reasons: List[str] = []

        if song.genre == user.favorite_genre:
            score += GENRE_MATCH_POINTS
            reasons.append(f"matches your favorite genre ({song.genre})")

        if song.mood == user.favorite_mood:
            score += MOOD_MATCH_POINTS
            reasons.append(f"matches your favorite mood ({song.mood})")

        energy_pts = _energy_similarity_points(user.target_energy, song.energy)
        score += energy_pts
        reasons.append(
            f"energy {song.energy:.2f} is close to your target {user.target_energy:.2f}"
            f" (+{energy_pts:.2f})"
        )

        if user.likes_acoustic and song.acousticness >= ACOUSTIC_THRESHOLD:
            score += ACOUSTIC_BONUS_POINTS
            reasons.append(f"acoustic sound you like (acousticness {song.acousticness:.2f})")

        return score, reasons

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """Return the top-k songs ranked by score, ties broken by popularity."""
        # Sort by score (desc), breaking ties with popularity so the ranking is
        # stable and predictable.
        ranked = sorted(
            self.songs,
            key=lambda s: (self._score(user, s)[0], s.popularity),
            reverse=True,
        )
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """Return a human-readable sentence explaining a song's score."""
        score, reasons = self._score(user, song)
        if not reasons:
            return f"'{song.title}' scored {score:.2f} with no strong matches."
        return (
            f"'{song.title}' scored {score:.2f} because it "
            + ", ".join(reasons)
            + "."
        )

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file into a list of dicts, converting numeric
    columns to numbers so the scoring logic can do math on them.
    Required by src/main.py
    """
    float_fields = {
        "energy", "tempo_bpm", "valence", "danceability",
        "acousticness", "instrumentalness",
    }
    int_fields = {"id", "popularity"}

    songs: List[Dict] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            song = dict(row)
            for key in float_fields:
                val = song.get(key)
                if val not in (None, ""):
                    song[key] = float(val)
            for key in int_fields:
                val = song.get(key)
                if val not in (None, ""):
                    song[key] = int(val)
            songs.append(song)
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences using the Phase 2 recipe:
        +2.0  genre match
        +1.0  mood match
        +1.5 * (1 - |target_energy - song_energy|)  energy similarity

    user_prefs is a dict with keys "genre", "mood", "energy".
    Returns (score, reasons).
    """
    score = 0.0
    reasons: List[str] = []

    if user_prefs.get("genre") is not None and song.get("genre") == user_prefs["genre"]:
        score += GENRE_MATCH_POINTS
        reasons.append(f"genre match: {song['genre']} (+{GENRE_MATCH_POINTS:.1f})")

    if user_prefs.get("mood") is not None and song.get("mood") == user_prefs["mood"]:
        score += MOOD_MATCH_POINTS
        reasons.append(f"mood match: {song['mood']} (+{MOOD_MATCH_POINTS:.1f})")

    target_energy = user_prefs.get("energy")
    if target_energy is not None and song.get("energy") is not None:
        energy_pts = _energy_similarity_points(target_energy, song["energy"])
        score += energy_pts
        reasons.append(
            f"energy similarity: {float(song['energy']):.2f} vs target"
            f" {float(target_energy):.2f} (+{energy_pts:.2f})"
        )

    return score, reasons

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Scores every song, ranks by score (ties broken by popularity), and returns
    the top k as (song_dict, score, explanation) tuples.
    Required by src/main.py
    """
    def evaluate(song: Dict) -> Tuple[Dict, float, str]:
        score, reasons = score_song(user_prefs, song)
        return song, score, ", ".join(reasons) if reasons else "no strong matches"

    scored = [evaluate(song) for song in songs]
    scored.sort(key=lambda item: (item[1], item[0].get("popularity", 0)), reverse=True)
    return scored[:k]
