"""
Priority Queue (Heap) for Merging Ordered Post Streams.
Governing Baseline: CC-PLN-DSA-002 v2.4, architecture.md v1.1, database.md v1.2.
"""

import heapq
from typing import List, Optional, Tuple, Dict, Any


class PostHeapEntry:
    """
    Heap entry wrapper ensuring exact equivalence to SQLite's
    ORDER BY created_at DESC, post_id DESC
    for TEXT ISO-8601 timestamps and TEXT UUID post_ids under BINARY collation.
    """

    __slots__ = ("created_at", "post_id", "stream_idx", "item_idx", "post")

    def __init__(self, post: Dict[str, Any], stream_idx: int, item_idx: int):
        self.created_at: str = post["created_at"]
        self.post_id: str = post["post_id"]
        self.stream_idx: int = stream_idx
        self.item_idx: int = item_idx
        self.post: Dict[str, Any] = post

    def __lt__(self, other: "PostHeapEntry") -> bool:
        # In a min-heap, A < B means A has higher priority and is popped first.
        # We want newer posts (greater created_at) to have higher priority.
        if self.created_at != other.created_at:
            return self.created_at > other.created_at
        # Equal timestamps: greater post_id (lexicographically / BINARY) has higher priority.
        return self.post_id > other.post_id


class HeapStreamMerger:
    """
    Merges k pre-sorted post streams into a single globally ordered stream
    using a min-heap priority queue in O(P log k) time.
    """

    @staticmethod
    def merge_post_streams(
        streams: List[List[Dict[str, Any]]],
        limit: int = 10,
        cursor: Optional[Tuple[str, str]] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[Tuple[str, str]]]:
        """
        Merge k pre-sorted streams of posts (each ordered created_at DESC, post_id DESC).

        Args:
            streams: List of pre-sorted author post streams.
            limit: Maximum number of posts to emit for this page.
            cursor: Optional (cursor_created_at, cursor_post_id) boundary from previous page.

        Returns:
            (merged_posts, next_cursor)
        """
        if limit <= 0 or not streams:
            return ([], None)

        # Step 1: Advance stream indices past cursor if a cursor is supplied
        # Condition: post must be strictly less than cursor in total order
        stream_pointers: list[int] = []
        for s in streams:
            idx = 0
            if cursor is not None:
                cur_ts, cur_id = cursor
                while idx < len(s):
                    p = s[idx]
                    p_ts, p_id = p["created_at"], p["post_id"]
                    # Strictly after cursor in DESC order means:
                    # p_ts < cur_ts OR (p_ts == cur_ts and p_id < cur_id)
                    if p_ts < cur_ts or (p_ts == cur_ts and p_id < cur_id):
                        break
                    idx += 1
            stream_pointers.append(idx)

        # Step 2: Populate heap with the head of each stream that has remaining items
        heap: list[PostHeapEntry] = []
        for s_idx, s in enumerate(streams):
            p_idx = stream_pointers[s_idx]
            if p_idx < len(s):
                heap.append(PostHeapEntry(s[p_idx], s_idx, p_idx))

        heapq.heapify(heap)

        merged_posts: list[dict[str, Any]] = []
        seen_post_ids: set[str] = set()

        # Step 3: K-way merge extraction loop
        while heap and len(merged_posts) < limit:
            entry = heapq.heappop(heap)

            # Deduplication protection: skip duplicate post_ids if same post appears across streams
            if entry.post_id not in seen_post_ids:
                seen_post_ids.add(entry.post_id)
                merged_posts.append(entry.post)

            # Advance this stream and push next item if available
            next_idx = entry.item_idx + 1
            stream = streams[entry.stream_idx]
            if next_idx < len(stream):
                heapq.heappush(heap, PostHeapEntry(stream[next_idx], entry.stream_idx, next_idx))

        # Step 4: Determine next cursor
        # If we reached the page limit and there are remaining items in the heap or streams,
        # emit the cursor for the last emitted post.
        next_cursor = None
        if len(merged_posts) == limit and heap:
            last_post = merged_posts[-1]
            next_cursor = (last_post["created_at"], last_post["post_id"])

        return (merged_posts, next_cursor)
