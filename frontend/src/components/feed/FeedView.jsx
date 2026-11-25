import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { api } from '../../services/api';
import { Button } from '../common/Button';
import { Avatar } from '../common/Avatar';

export function FeedView({ onSelectUser }) {
  const { currentUser } = useAuth();
  const { showToast } = useToast();
  const [posts, setPosts] = useState([]);
  const [nextCursor, setNextCursor] = useState(null);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [postContent, setPostContent] = useState('');
  const [submittingPost, setSubmittingPost] = useState(false);

  const fetchFeed = useCallback(async (cursor = null, isInitial = false) => {
    try {
      if (isInitial) setLoading(true);
      else setLoadingMore(true);

      const endpoint = cursor ? `/feed?limit=10&cursor=${encodeURIComponent(cursor)}` : '/feed?limit=10';
      const res = await api.get(endpoint);

      if (res?.success && res?.data) {
        const newPosts = res.data.posts || [];
        setPosts((prev) => (isInitial ? newPosts : [...prev, ...newPosts]));
        setNextCursor(res.data.next_cursor || null);
        setHasMore(!!res.data.has_more);
      }
    } catch (err) {
      showToast(err.message || 'Failed to load feed', 'error');
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchFeed(null, true);
  }, [fetchFeed]);

  const handleCreatePost = async (e) => {
    e.preventDefault();
    if (!postContent.trim()) return;

    try {
      setSubmittingPost(true);
      const res = await api.post('/posts', { content: postContent.trim() });
      if (res?.success) {
        showToast('Dispatch shared with your campus network');
        setPostContent('');
        fetchFeed(null, true);
      }
    } catch (err) {
      showToast(err.message || 'Failed to publish post', 'error');
    } finally {
      setSubmittingPost(false);
    }
  };

  const handleDeletePost = async (postId) => {
    if (!window.confirm('Are you sure you want to delete this post?')) return;

    try {
      await api.delete(`/posts/${postId}`);
      showToast('Post removed from campus stream');
      setPosts((prev) => prev.filter((p) => (p.post_id || p.id) !== postId));
    } catch (err) {
      showToast(err.message || 'Failed to delete post', 'error');
    }
  };

  const formatTimestamp = (isoString) => {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="max-w-2xl w-full mx-auto lg:mx-0 space-y-6">
      {/* 1. Page Header */}
      <header className="pb-3 border-b border-soft-sand/80 flex items-baseline justify-between gap-3">
        <div>
          <h1 className="text-xl sm:text-2xl font-serif font-bold text-shadow-grey tracking-tight">
            Campus Feed
          </h1>
          <p className="text-xs sm:text-sm text-iron-grey font-sans mt-0.5">
            Academic notes, project updates, and discussions from your university network.
          </p>
        </div>
        <div className="hidden sm:flex items-center gap-1.5 text-[11px] font-sans text-iron-grey/80 bg-soft-sand/40 px-2.5 py-1 rounded-full border border-soft-sand/60 shrink-0">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 inline-block animate-pulse"></span>
          <span>Live Stream</span>
        </div>
      </header>

      {/* 2. Post Composer */}
      <section aria-label="Create a post" className="bg-white rounded-xl border border-soft-sand/90 shadow-subtle p-4 sm:p-5 focus-within:border-iron-grey/40 focus-within:shadow-card transition-all duration-200">
        <form onSubmit={handleCreatePost}>
          <div className="flex items-start gap-3.5">
            <Avatar
              name={currentUser?.full_name || currentUser?.username}
              size="md"
              className="shrink-0 mt-0.5 ring-2 ring-soft-sand/50"
            />
            <div className="flex-1 min-w-0">
              <label htmlFor="feed-post-composer" className="sr-only">
                Write a dispatch or update
              </label>
              <textarea
                id="feed-post-composer"
                name="content"
                value={postContent}
                onChange={(e) => setPostContent(e.target.value)}
                placeholder="Share a research finding, project update, or discussion topic..."
                rows={3}
                maxLength={1000}
                className="w-full bg-warm-porcelain/40 focus:bg-white text-sm sm:text-[15px] text-shadow-grey placeholder:text-iron-grey/50 rounded-lg p-3.5 border border-soft-sand/80 focus:border-iron-grey/40 focus:outline-none focus:ring-1 focus:ring-iron-grey/25 resize-none transition-all leading-relaxed font-sans"
              />
              <div className="flex items-center justify-between mt-3 pt-2.5 border-t border-soft-sand/60">
                <span
                  className={`text-xs font-sans tabular-nums transition-colors ${
                    postContent.length > 900 ? 'text-deep-crimson font-medium' : 'text-iron-grey/70'
                  }`}
                >
                  {postContent.length} / 1000
                </span>
                <Button
                  type="submit"
                  size="sm"
                  disabled={!postContent.trim() || submittingPost}
                  loading={submittingPost}
                  className="font-medium px-4 shadow-subtle"
                >
                  Publish Post
                </Button>
              </div>
            </div>
          </div>
        </form>
      </section>

      {/* 3. Post Feed Stream */}
      {loading ? (
        <div className="space-y-4" aria-label="Loading posts">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-soft-sand/70 p-5 sm:p-6 space-y-3.5 animate-pulse"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-soft-sand/70 shrink-0"></div>
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="h-3.5 bg-soft-sand/70 rounded w-36"></div>
                  <div className="h-2.5 bg-soft-sand/40 rounded w-24"></div>
                </div>
              </div>
              <div className="sm:pl-[52px] space-y-2">
                <div className="h-3.5 bg-soft-sand/60 rounded w-full"></div>
                <div className="h-3.5 bg-soft-sand/60 rounded w-4/5"></div>
                <div className="h-3.5 bg-soft-sand/40 rounded w-2/3"></div>
              </div>
            </div>
          ))}
        </div>
      ) : posts.length === 0 ? (
        /* 4. Empty State */
        <div className="bg-white/80 border border-soft-sand rounded-xl p-8 sm:p-12 text-center shadow-subtle">
          <div className="w-12 h-12 mx-auto mb-3.5 rounded-full bg-soft-sand/50 border border-soft-sand/80 flex items-center justify-center text-iron-grey">
            <svg
              className="w-6 h-6 stroke-iron-grey"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth="1.5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M12 7.5h1.5m-1.5 3h1.5m-7.5 3h7.5m-7.5 3h7.5m3-9h3.375c.621 0 1.125.504 1.125 1.125V18a2.25 2.25 0 01-2.25 2.25M16.5 7.5V18a2.25 2.25 0 002.25 2.25M16.5 7.5V4.875c0-.621-.504-1.125-1.125-1.125H4.125C3.504 3.75 3 4.254 3 4.875V18a2.25 2.25 0 002.25 2.25h13.5M6 7.5h3v3H6v-3z"
              />
            </svg>
          </div>
          <h2 className="text-base sm:text-lg font-serif font-bold text-shadow-grey mb-1.5">
            Your campus feed is currently quiet
          </h2>
          <p className="text-xs sm:text-sm text-iron-grey max-w-md mx-auto leading-relaxed font-sans mb-4">
            Dispatches from you and your accepted peer connections will appear in this real-time stream. Share your first academic note above or discover classmates to broaden your network.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {posts.map((post) => {
            const postId = post.post_id || post.id;
            const author = post.author || {};
            const isOwnPost = (post.user_id || author.user_id) === currentUser?.user_id;

            return (
              <article
                key={postId}
                className="bg-white rounded-xl border border-soft-sand/80 p-5 sm:p-6 shadow-[0_1px_3px_0_rgba(39,40,56,0.03)] hover:border-soft-sand hover:shadow-subtle transition-all duration-150"
              >
                {/* Author Metadata Header */}
                <div className="flex items-start justify-between gap-3">
                  <div
                    className="flex items-center gap-3 cursor-pointer group min-w-0"
                    onClick={() => onSelectUser && onSelectUser(post.user_id || author.user_id)}
                  >
                    <Avatar
                      name={author.full_name || author.username}
                      size="md"
                      className="shrink-0 transition-transform group-hover:scale-105 ring-1 ring-soft-sand/60"
                    />
                    <div className="min-w-0">
                      <h3 className="text-sm sm:text-[15px] font-semibold text-shadow-grey group-hover:text-deep-crimson transition-colors truncate font-sans">
                        {author.full_name || author.username || 'Student'}
                      </h3>
                      <p className="text-xs text-iron-grey/80 truncate font-sans">
                        @{author.username} <span className="mx-1 text-soft-sand/90">&middot;</span> {formatTimestamp(post.created_at)}
                      </p>
                    </div>
                  </div>

                  {/* Discreet Delete Action for Post Author */}
                  {isOwnPost && (
                    <button
                      type="button"
                      onClick={() => handleDeletePost(postId)}
                      className="text-xs text-iron-grey/60 hover:text-deep-crimson hover:bg-soft-sand/40 px-2 py-1 rounded transition-colors shrink-0 flex items-center gap-1 font-sans"
                      title="Delete your post"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="1.8"
                          d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                        />
                      </svg>
                      <span>Delete</span>
                    </button>
                  )}
                </div>

                {/* Post Content Body in Newsreader Serif */}
                <div className="mt-3.5 sm:pl-[52px]">
                  <p className="text-[15px] sm:text-base font-serif text-shadow-grey/95 leading-relaxed whitespace-pre-wrap break-words">
                    {post.content}
                  </p>
                </div>
              </article>
            );
          })}

          {/* Min-Heap Feed Stream Pagination */}
          {hasMore && (
            <div className="text-center pt-3 pb-2">
              <Button
                variant="outline"
                size="md"
                onClick={() => fetchFeed(nextCursor, false)}
                loading={loadingMore}
                disabled={loadingMore}
                className="font-medium text-xs sm:text-sm px-6 hover:border-iron-grey/40"
              >
                Load Older Dispatches
              </Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
