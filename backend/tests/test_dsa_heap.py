"""
Unit tests for PostHeapEntry comparison and HeapStreamMerger cursor pagination.
"""

from app.dsa.heap import PostHeapEntry, HeapStreamMerger


def test_post_heap_entry_comparison():
    # Newer timestamp must compare as < (higher priority in min-heap)
    newer = PostHeapEntry(
        {"post_id": "p1", "created_at": "2026-11-13T12:00:00.000000Z"},
        stream_idx=0,
        item_idx=0
    )
    older = PostHeapEntry(
        {"post_id": "p2", "created_at": "2026-11-13T11:00:00.000000Z"},
        stream_idx=0,
        item_idx=1
    )
    assert newer < older

    # Equal timestamps: greater post_id (lexicographical BINARY collation) has higher priority
    p_high = PostHeapEntry(
        {"post_id": "post_b", "created_at": "2026-11-13T12:00:00.000000Z"},
        stream_idx=0,
        item_idx=0
    )
    p_low = PostHeapEntry(
        {"post_id": "post_a", "created_at": "2026-11-13T12:00:00.000000Z"},
        stream_idx=1,
        item_idx=0
    )
    assert p_high < p_low


def test_heap_stream_merger_equal_timestamps_match_sqlite_binary_order():
    """
    Verify equal-timestamp tie breaking produces the exact same deterministic sequence
    as SQLite's ORDER BY created_at DESC, post_id DESC.
    """
    shared_ts = "2026-11-13T12:00:00.000000Z"
    stream_1 = [
        {"post_id": "uuid_3", "created_at": shared_ts, "content": "from s1"},
        {"post_id": "uuid_1", "created_at": shared_ts, "content": "from s1"},
    ]
    stream_2 = [
        {"post_id": "uuid_4", "created_at": shared_ts, "content": "from s2"},
        {"post_id": "uuid_2", "created_at": shared_ts, "content": "from s2"},
    ]

    merged, next_cur = HeapStreamMerger.merge_post_streams([stream_1, stream_2], limit=10)
    merged_ids = [p["post_id"] for p in merged]

    # SQLite ORDER BY created_at DESC, post_id DESC yields uuid_4, uuid_3, uuid_2, uuid_1
    assert merged_ids == ["uuid_4", "uuid_3", "uuid_2", "uuid_1"]
    assert next_cur is None


def test_heap_stream_merger_deduplicates_posts():
    """Verify same post appearing in multiple streams is deduplicated."""
    shared_post = {"post_id": "shared_p1", "created_at": "2026-11-13T12:00:00.000000Z"}
    stream_1 = [shared_post]
    stream_2 = [shared_post]

    merged, _ = HeapStreamMerger.merge_post_streams([stream_1, stream_2], limit=10)
    assert len(merged) == 1
    assert merged[0]["post_id"] == "shared_p1"


def test_heap_cursor_pagination_zero_duplicates_and_zero_skips():
    """
    Test paginating through 50 posts distributed across 3 author streams (limit=10 per page).
    Assert zero duplicate posts and zero skipped posts across all 5 pages.
    """
    # Generate 50 posts with descending timestamps
    all_posts = []
    for i in range(50, 0, -1):
        all_posts.append({
            "post_id": f"p_{i:03d}",
            "created_at": f"2026-11-13T12:{i:02d}:00.000000Z",
            "content": f"Post {i}"
        })

    # Distribute across 3 author streams (each sorted DESC)
    stream_a = [p for idx, p in enumerate(all_posts) if idx % 3 == 0]
    stream_b = [p for idx, p in enumerate(all_posts) if idx % 3 == 1]
    stream_c = [p for idx, p in enumerate(all_posts) if idx % 3 == 2]

    # Page through with limit=10
    collected_posts = []
    cursor = None
    page_count = 0

    while True:
        page_posts, cursor = HeapStreamMerger.merge_post_streams(
            [stream_a, stream_b, stream_c],
            limit=10,
            cursor=cursor
        )
        if not page_posts:
            break
        collected_posts.extend(page_posts)
        page_count += 1
        if cursor is None:
            break

    assert page_count == 5
    assert len(collected_posts) == 50

    # Verify zero duplicate post IDs
    collected_ids = [p["post_id"] for p in collected_posts]
    assert len(collected_ids) == len(set(collected_ids))

    # Verify complete collection matches all 50 original posts in exact order
    expected_ids = [p["post_id"] for p in all_posts]
    assert collected_ids == expected_ids
