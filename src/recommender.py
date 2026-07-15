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
    # Baseline extras (defaults keep existing Song(...) calls and tests valid)
    instrumentalness: float = 0.0   # 0.0 = vocal-forward, 1.0 = purely instrumental
    popularity: int = 0             # 0-100; useful as a ranking tie-breaker
    # --- Challenge 1: advanced features (all optional, so tests stay valid) ---
    release_decade: int = 0         # e.g. 1990, 2000, 2010, 2020
    mood_tags: str = ""             # extra vibe tags, ";"-separated (e.g. "hype;bold")
    language: str = ""              # english / spanish / instrumental
    explicit: int = 0               # 0 = clean, 1 = explicit lyrics
    duration_sec: int = 0           # track length in seconds

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
    # Optional advanced preferences (default off, so existing tests stay valid)
    preferred_decade: Optional[int] = None
    preferred_language: Optional[str] = None
    avoid_explicit: bool = False

# --- Scoring Recipe (Phase 2) -------------------------------------------------
# Base point weights, tuned to the diversity of data/songs.csv. See README for
# the reasoning behind each weight.
GENRE_MATCH_POINTS = 2.0
MOOD_MATCH_POINTS = 1.0
ENERGY_SIMILARITY_WEIGHT = 1.5
ACOUSTIC_BONUS_POINTS = 0.5
ACOUSTIC_THRESHOLD = 0.6

# --- Challenge 1: weights for the advanced features --------------------------
DECADE_MATCH_POINTS = 0.75      # song came from the era you like
MOOD_TAG_POINTS = 0.5           # song carries a secondary vibe tag you asked for
LANGUAGE_MATCH_POINTS = 0.5     # song language matches your preference
EXPLICIT_PENALTY = 1.0          # subtracted if you avoid explicit and the song is
LENGTH_MATCH_POINTS = 0.5       # track length fits the size you like

# --- Challenge 2: scoring modes (a lightweight Strategy pattern) --------------
# Each mode is a "strategy": the SAME algorithm runs, but the weights on the
# three core signals change, so the ranking leans a different way. "balanced"
# reproduces the original recipe exactly, so existing tests/output are unchanged.
SCORING_MODES: Dict[str, Dict[str, float]] = {
    "balanced":       {"genre": GENRE_MATCH_POINTS, "mood": MOOD_MATCH_POINTS, "energy": ENERGY_SIMILARITY_WEIGHT},
    "genre_first":    {"genre": 3.0, "mood": 0.5, "energy": 0.5},
    "mood_first":     {"genre": 0.5, "mood": 3.0, "energy": 1.0},
    "energy_focused": {"genre": 0.5, "mood": 0.5, "energy": 3.0},
}


def _energy_similarity_points(target_energy: float, song_energy: float, weight: float = ENERGY_SIMILARITY_WEIGHT) -> float:
    """Graded points (0 -> weight) for how close energy is."""
    closeness = 1.0 - abs(float(target_energy) - float(song_energy))
    return weight * closeness


def _signed(points: float) -> str:
    """Format points with a correct sign, so a penalty reads '-1.00' not '+-1.00'."""
    return f"+{points:.2f}" if points >= 0 else f"{points:.2f}"


def _length_category(duration_sec: float) -> str:
    """Bucket a track length into short / medium / long."""
    if duration_sec and duration_sec < 200:
        return "short"
    if duration_sec and duration_sec <= 240:
        return "medium"
    return "long"


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score(self, user: UserProfile, song: Song, mode: str = "balanced") -> Tuple[float, List[str]]:
        """Return (score, reasons) for one song under the chosen scoring mode."""
        weights = SCORING_MODES.get(mode, SCORING_MODES["balanced"])
        score = 0.0
        reasons: List[str] = []

        if song.genre == user.favorite_genre:
            score += weights["genre"]
            reasons.append(f"matches your favorite genre ({song.genre})")

        if song.mood == user.favorite_mood:
            score += weights["mood"]
            reasons.append(f"matches your favorite mood ({song.mood})")

        energy_pts = _energy_similarity_points(user.target_energy, song.energy, weights["energy"])
        score += energy_pts
        reasons.append(
            f"energy {song.energy:.2f} is close to your target {user.target_energy:.2f}"
            f" ({_signed(energy_pts)})"
        )

        if user.likes_acoustic and song.acousticness >= ACOUSTIC_THRESHOLD:
            score += ACOUSTIC_BONUS_POINTS
            reasons.append(f"acoustic sound you like (acousticness {song.acousticness:.2f})")

        if user.preferred_decade is not None and song.release_decade == user.preferred_decade:
            score += DECADE_MATCH_POINTS
            reasons.append(f"from the {song.release_decade}s era you like ({_signed(DECADE_MATCH_POINTS)})")

        if user.preferred_language and song.language == user.preferred_language:
            score += LANGUAGE_MATCH_POINTS
            reasons.append(f"language match: {song.language} ({_signed(LANGUAGE_MATCH_POINTS)})")

        if user.avoid_explicit and song.explicit:
            score -= EXPLICIT_PENALTY
            reasons.append(f"explicit track you avoid ({_signed(-EXPLICIT_PENALTY)})")

        return score, reasons

    def recommend(self, user: UserProfile, k: int = 5, mode: str = "balanced") -> List[Song]:
        """Return the top-k songs ranked by score, ties broken by popularity."""
        ranked = sorted(
            self.songs,
            key=lambda s: (self._score(user, s, mode)[0], s.popularity),
            reverse=True,
        )
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song, mode: str = "balanced") -> str:
        """Return a human-readable sentence explaining a song's score."""
        score, reasons = self._score(user, song, mode)
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
    int_fields = {"id", "popularity", "release_decade", "explicit", "duration_sec"}

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

def score_song(user_prefs: Dict, song: Dict, mode: str = "balanced") -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.

    Core signals (weighted by the chosen `mode`):
        genre match, mood match, energy similarity = weight * (1 - |Δenergy|)

    Advanced signals (Challenge 1, only applied when the pref is present):
        decade match, secondary mood tag, language match, explicit penalty,
        track-length preference.

    Returns (score, reasons).
    """
    weights = SCORING_MODES.get(mode, SCORING_MODES["balanced"])
    score = 0.0
    reasons: List[str] = []

    if user_prefs.get("genre") is not None and song.get("genre") == user_prefs["genre"]:
        score += weights["genre"]
        reasons.append(f"genre match: {song['genre']} (+{weights['genre']:.1f})")

    if user_prefs.get("mood") is not None and song.get("mood") == user_prefs["mood"]:
        score += weights["mood"]
        reasons.append(f"mood match: {song['mood']} (+{weights['mood']:.1f})")

    target_energy = user_prefs.get("energy")
    if target_energy is not None and song.get("energy") is not None:
        energy_pts = _energy_similarity_points(target_energy, song["energy"], weights["energy"])
        score += energy_pts
        reasons.append(
            f"energy similarity: {float(song['energy']):.2f} vs target"
            f" {float(target_energy):.2f} ({_signed(energy_pts)})"
        )

    # --- Advanced features (Challenge 1) -------------------------------------
    decade = user_prefs.get("decade")
    if decade is not None and song.get("release_decade") not in (None, "", 0) \
            and int(song["release_decade"]) == int(decade):
        score += DECADE_MATCH_POINTS
        reasons.append(f"era match: {song['release_decade']}s ({_signed(DECADE_MATCH_POINTS)})")

    wanted_tag = user_prefs.get("mood_tag")
    if wanted_tag:
        tags = [t.strip() for t in str(song.get("mood_tags", "")).split(";") if t.strip()]
        if wanted_tag in tags:
            score += MOOD_TAG_POINTS
            reasons.append(f"vibe tag match: '{wanted_tag}' ({_signed(MOOD_TAG_POINTS)})")

    language = user_prefs.get("language")
    if language and song.get("language") == language:
        score += LANGUAGE_MATCH_POINTS
        reasons.append(f"language match: {language} ({_signed(LANGUAGE_MATCH_POINTS)})")

    if user_prefs.get("avoid_explicit") and int(song.get("explicit", 0) or 0):
        score -= EXPLICIT_PENALTY
        reasons.append(f"explicit lyrics you avoid ({_signed(-EXPLICIT_PENALTY)})")

    length = user_prefs.get("length")
    if length and song.get("duration_sec"):
        if _length_category(float(song["duration_sec"])) == length:
            score += LENGTH_MATCH_POINTS
            reasons.append(f"length fits '{length}' ({_signed(LENGTH_MATCH_POINTS)})")

    return score, reasons

def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    mode: str = "balanced",
    artist_penalty: float = 0.0,
    genre_penalty: float = 0.0,
) -> List[Tuple[Dict, float, str]]:
    """
    Scores every song and returns the top k as (song, score, explanation) tuples.

    Ranking:
      * By default (no penalties) songs are sorted by score, ties broken by
        popularity -- the original behavior.
      * Challenge 3: when artist_penalty/genre_penalty > 0, selection is greedy
        and diversity-aware. Each time a song is chosen, any remaining song that
        shares its artist (or genre) is docked points, so the top list can't be
        dominated by one artist or genre. See the diversity rule in the README.
    """
    scored: List[Tuple[Dict, float, List[str]]] = []
    for song in songs:
        s, reasons = score_song(user_prefs, song, mode)
        scored.append((song, s, reasons))

    # Simple path: no diversity logic requested.
    if artist_penalty <= 0 and genre_penalty <= 0:
        scored.sort(key=lambda item: (item[1], item[0].get("popularity", 0)), reverse=True)
        return [(song, s, ", ".join(r) if r else "no strong matches") for song, s, r in scored[:k]]

    # Greedy diversity-aware selection.
    remaining = list(scored)
    chosen: List[Tuple[Dict, float, str]] = []
    seen_artists: List[str] = []
    seen_genres: List[str] = []

    while remaining and len(chosen) < k:
        best_idx = -1
        best_adj = float("-inf")
        best_pen = 0.0
        for i, (song, base, _reasons) in enumerate(remaining):
            pen = artist_penalty * seen_artists.count(song.get("artist")) \
                + genre_penalty * seen_genres.count(song.get("genre"))
            adj = base - pen
            # Tie-break on popularity, like the simple path.
            better = adj > best_adj or (
                adj == best_adj and best_idx >= 0
                and song.get("popularity", 0) > remaining[best_idx][0].get("popularity", 0)
            )
            if better:
                best_idx, best_adj, best_pen = i, adj, pen

        song, base, reasons = remaining.pop(best_idx)
        parts = list(reasons) if reasons else ["no strong matches"]
        if best_pen > 0:
            parts.append(
                f"diversity penalty -{best_pen:.2f} (artist/genre already in list)"
            )
        chosen.append((song, best_adj, ", ".join(parts)))
        seen_artists.append(song.get("artist"))
        seen_genres.append(song.get("genre"))

    return chosen
