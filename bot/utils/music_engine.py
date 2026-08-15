import json
import logging
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler

from config import config

logger = logging.getLogger(__name__)

FEATURE_COLUMNS = [
    "popularity", "danceability", "energy", "key", "loudness", "mode",
    "speechiness", "acousticness", "instrumentalness", "liveness", "valence", "tempo",
]


class MusicEngine:
    def __init__(self, dataset_path: str):
        self.available = False
        try:
            self.df = pd.read_csv(dataset_path)
            self.df = self.df.drop_duplicates(subset=["track_name", "artists"]).reset_index(drop=True)
            features = self.df[FEATURE_COLUMNS].apply(pd.to_numeric, errors="coerce").fillna(0)
            scaler = MinMaxScaler()
            self.scaled = pd.DataFrame(scaler.fit_transform(features), columns=FEATURE_COLUMNS, index=self.df.index)
            self.available = True
            logger.info(f"MusicEngine loaded {len(self.df)} tracks")
        except Exception as e:
            logger.warning(f"MusicEngine dataset not loaded: {e}")
            self.df = pd.DataFrame(columns=["track_name", "artists", "track_genre"])
            self.scaled = pd.DataFrame(columns=FEATURE_COLUMNS)

    def search_track(self, track_name: str, artist: Optional[str] = None) -> Optional[dict]:
        if not self.available or not track_name:
            return None
        mask = self.df["track_name"].str.contains(track_name, case=False, na=False, regex=False)
        if artist:
            mask &= self.df["artists"].str.lower() == artist.lower()
        matches = self.df[mask]
        if matches.empty:
            return None
        best = matches.sort_values("popularity", ascending=False).iloc[0]
        return {
            "index": int(best.name),
            "track_name": str(best["track_name"]),
            "artist": str(best["artists"]),
            "genre": str(best["track_genre"]),
        }

    def get_track_vector(self, index: int) -> Optional[List[float]]:
        if not self.available or index not in self.scaled.index:
            return None
        return self.scaled.loc[index].tolist()

    def build_taste_vector(self, indices: List[int]) -> Optional[List[float]]:
        vectors = [self.get_track_vector(i) for i in indices]
        vectors = [v for v in vectors if v is not None]
        if not vectors:
            return None
        return np.mean(vectors, axis=0).tolist()

    @staticmethod
    def similarity(vec_a: Optional[list], vec_b: Optional[list]) -> float:
        if not vec_a or not vec_b:
            return 0.0
        a = np.array(vec_a).reshape(1, -1)
        b = np.array(vec_b).reshape(1, -1)
        return float(cosine_similarity(a, b)[0][0])


def resolve_tracks(names: List[str]):
    matched, unmatched = [], []
    for name in names:
        name = name.strip()
        if not name:
            continue
        result = engine.search_track(name)
        if result:
            matched.append(result)
        else:
            unmatched.append(name)
    return matched, unmatched


def vector_to_json(vector: Optional[list]) -> Optional[str]:
    return json.dumps(vector) if vector else None


def vector_from_json(data: Optional[str]) -> Optional[list]:
    return json.loads(data) if data else None


engine = MusicEngine(config.MUSIC_DATASET_PATH)
