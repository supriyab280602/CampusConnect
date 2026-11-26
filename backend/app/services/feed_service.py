import base64
import sqlite3
from typing import Any, Dict, List, Optional, Tuple
from app.db.connection import get_db
from app.dsa import get_dsa_manager
from app.dsa.heap import HeapStreamMerger
from app.repositories.post_repository import PostRepository
from app.repositories.user_repository import UserRepository


def encode_cursor(created_at: str, post_id: str) -> str:
    """Encode (created_at, post_id) into a URL-safe cursor string."""
    raw = f"{created_at}|{post_id}"
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("utf-8")


def decode_cursor(cursor_str: str) -> Optional[Tuple[str, str]]:
    """Decode URL-safe cursor string into (created_at, post_id)."""
    if not cursor_str:
        return None
    try:
        raw = base64.urlsafe_b64decode(cursor_str.encode("utf-8")).decode("utf-8")
        parts = raw.split("|", 1)
        if len(parts) == 2 and parts[0].strip() and parts[1].strip():
            return parts[0], parts[1]
    except Exception:
        pass
    raise ValueError("Invalid pagination cursor.")


class FeedService:
    """
    Service building personalized student post feed.
    Merges ordered post streams of accepted connections and self using min-heap priority queue.
    """

    @staticmethod
    def get_feed(
        user_id: str,
        limit: int = 10,
        cursor_str: Optional[str] = None,
        conn: Optional[sqlite3.Connection] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve paginated feed of posts from the user and their accepted connections.
        Merges streams using O(P log k) heap-based k-way merge.
        """
        limit = max(1, min(limit, 50))
        conn = conn or get_db()
        dsa_manager = get_dsa_manager()

        # Step 1: Identify accepted connections from in-memory graph
        connected_ids = dsa_manager.get_neighbors(user_id)

        # Authors = user + accepted connections
        author_ids = list(set([user_id] + list(connected_ids)))

        # Step 2: Decode pagination cursor
        parsed_cursor = decode_cursor(cursor_str) if cursor_str else None
        before_ts, before_id = parsed_cursor if parsed_cursor else (None, None)

        # Step 3: Fetch sorted author post streams (ORDER BY created_at DESC, post_id DESC)
        streams: List[List[Dict[str, Any]]] = []
        for author_id in author_ids:
            author_posts = PostRepository.get_posts_by_user(
                conn=conn,
                user_id=author_id,
                limit=limit + 1,  # buffer for cursor alignment
                before_timestamp=before_ts,
                before_post_id=before_id,
            )
            if author_posts:
                streams.append(author_posts)

        # Step 4: K-way merge using HeapStreamMerger
        merged_posts, next_raw_cursor = HeapStreamMerger.merge_post_streams(
            streams=streams,
            limit=limit,
            cursor=parsed_cursor,
        )

        # Step 5: Enrich posts with author information
        enriched = []
        author_cache = {}
        for p in merged_posts:
            aid = p["user_id"]
            if aid not in author_cache:
                author_cache[aid] = UserRepository.get_by_id(conn, aid)
            author = author_cache[aid]

            enriched.append({
                "post_id": p["post_id"],
                "user_id": p["user_id"],
                "content": p["content"],
                "created_at": p["created_at"],
                "author": {
                    "user_id": author["user_id"],
                    "username": author["username"],
                    "full_name": author["full_name"],
                    "programme": author.get("programme"),
                    "academic_year": author.get("academic_year"),
                } if author else None,
            })

        next_cursor_encoded = (
            encode_cursor(next_raw_cursor[0], next_raw_cursor[1])
            if next_raw_cursor
            else None
        )

        return {
            "posts": enriched,
            "next_cursor": next_cursor_encoded,
            "has_more": next_cursor_encoded is not None,
        }

