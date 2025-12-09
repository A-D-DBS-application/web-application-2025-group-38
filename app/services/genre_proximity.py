"""utilities computing genre proximity using co-occurence graph"""

import heapq
from typing import Dict, Iterable, List, Mapping, MutableMapping, Set

from sqlalchemy import func
from sqlalchemy.orm import aliased

from models import db, Genres, ArtistGenres

ANCHOR_DISTANCE = 0.5 #non-overpowering
def build_genre_graph() -> MutableMapping[int, List[tuple[int, float]]]:
    """
    Build a weighted, undirected graph connecting genres that co-occur on the same artist.

    A lower edge weight indicates a stronger relationship because distances are the
    inverse of the co-occurrence count. The graph is sparse and only connects genres
    that have actually been observed together.
    """
    
    graph: MutableMapping[int, List[tuple[int, float]]] = {}
    g1 = aliased(ArtistGenres)
    g2 = aliased(ArtistGenres)

    for left, right, weight in (
        db.session.query(
            g1.genre_id,
            g2.genre_id,
            func.count().label("pair_count"),
        )
        .filter(g1.artist_id == g2.artist_id, g1.genre_id < g2.genre_id)
        .group_by(g1.genre_id, g2.genre_id)
    ):
        distance = 1 / (1 + float(weight))
        graph.setdefault(left, []).append((right, distance))
        graph.setdefault(right, []).append((left, distance))
    
    manual_links = (
        db.session.query(Genres.id, Genres.related_genre_id)
        .filter(Genres.related_genre_id.isnot(None))
        .all()
    )

    for genre_id, related_id in manual_links:
        if genre_id == related_id:
            continue

        graph.setdefault(genre_id, []).append((related_id, ANCHOR_DISTANCE))
        graph.setdefault(related_id, []).append((genre_id, ANCHOR_DISTANCE))
    return graph


def _dijkstra_multi_source(
    graph: Mapping[int, List[tuple[int, float]]], start: Set[int]
) -> Dict[int, float]:
    """Compute the shortest distances from multiple source genres using Dijkstra."""

    distances: Dict[int, float] = {node: 0.0 for node in start}
    queue: list[tuple[float, int]] = [(0.0, node) for node in start]
    heapq.heapify(queue)

    while queue:
        cost, node = heapq.heappop(queue)
        if cost > distances.get(node, float("inf")):
            continue

        for neighbor, weight in graph.get(node, []):
            new_cost = cost + weight
            if new_cost < distances.get(neighbor, float("inf")):
                distances[neighbor] = new_cost
                heapq.heappush(queue, (new_cost, neighbor))

    return distances


def genre_proximity_scores(preferred_genre_names: Iterable[str]) -> Dict[int, float]:
    """
    Convert user-preferred genres into proximity scores for all known genres.

    The closer a genre is to the user's favourites in the genre graph, the higher
    the resulting score (scaled between 0 and 1).
    """

    if not preferred_genre_names:
        return {}

    preferred_genres = {
        genre.id for genre in Genres.query.filter(Genres.name.in_(set(preferred_genre_names)))
    }
    if not preferred_genres:
        return {}

    graph = build_genre_graph()
    distances = _dijkstra_multi_source(graph, preferred_genres)
    if not distances:
        return {}

    farthest = max(distances.values())
    if farthest == 0:
        return {gid: 1.0 for gid in distances}

    return {gid: 1 - (dist / farthest) for gid, dist in distances.items()}