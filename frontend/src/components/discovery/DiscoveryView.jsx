import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { api } from '../../services/api';
import { Button } from '../common/Button';
import { Avatar } from '../common/Avatar';

export function DiscoveryView({ onSelectUser }) {
  const { currentUser } = useAuth();
  const { showToast } = useToast();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(true);
  const [sendingId, setSendingId] = useState(null);

  // Live relationship tracking from backend
  const [connectedIds, setConnectedIds] = useState(new Set());
  const [pendingSentIds, setPendingSentIds] = useState(new Set());
  const [pendingReceivedIds, setPendingReceivedIds] = useState(new Set());
  const [recommendations, setRecommendations] = useState([]);

  // Load real relationships and initial graph recommendations on mount
  const loadInitialContext = useCallback(async () => {
    try {
      setInitialLoading(true);
      const [connsRes, sentRes, receivedRes, recsRes] = await Promise.allSettled([
        api.get('/connections'),
        api.get('/connections/requests/sent'),
        api.get('/connections/requests/received'),
        api.get('/network/recommendations?limit=6'),
      ]);

      if (connsRes.status === 'fulfilled' && connsRes.value?.success) {
        const conns = connsRes.value.data?.connections || [];
        const set = new Set(
          conns.map((c) => c.user_id || c.id || c.user?.user_id).filter(Boolean)
        );
        setConnectedIds(set);
      }

      if (sentRes.status === 'fulfilled' && sentRes.value?.success) {
        const sent = sentRes.value.data?.requests || [];
        const set = new Set(
          sent
            .filter((r) => !r.status || r.status === 'pending')
            .map((r) => r.receiver_id || r.receiver?.user_id)
            .filter(Boolean)
        );
        setPendingSentIds(set);
      }

      if (receivedRes.status === 'fulfilled' && receivedRes.value?.success) {
        const rec = receivedRes.value.data?.requests || [];
        const set = new Set(
          rec
            .filter((r) => !r.status || r.status === 'pending')
            .map((r) => r.sender_id || r.sender?.user_id)
            .filter(Boolean)
        );
        setPendingReceivedIds(set);
      }

      if (recsRes.status === 'fulfilled' && recsRes.value?.success) {
        setRecommendations(recsRes.value.data?.recommendations || []);
      }
    } catch (err) {
      console.error('Failed to load initial discovery context', err);
    } finally {
      setInitialLoading(false);
    }
  }, []);

  useEffect(() => {
    loadInitialContext();
  }, [loadInitialContext]);

  // Debounced prefix lookup via custom Trie endpoint
  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      setLoading(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setLoading(true);
        const res = await api.get(`/search/users?q=${encodeURIComponent(query.trim())}&limit=20`);
        if (res?.success && res?.data?.results) {
          setResults(res.data.results);
        }
      } catch (err) {
        showToast(err.message || 'Search failed', 'error');
      } finally {
        setLoading(false);
      }
    }, 200);

    return () => clearTimeout(timer);
  }, [query, showToast]);

  const handleSendRequest = async (targetUserId) => {
    try {
      setSendingId(targetUserId);
      const res = await api.post('/connections/requests', { receiver_id: targetUserId });
      if (res?.success) {
        showToast('Connection request sent');
        setPendingSentIds((prev) => new Set([...prev, targetUserId]));
      }
    } catch (err) {
      const msg = err.message || '';
      if (msg.toLowerCase().includes('pending') || msg.toLowerCase().includes('already exists')) {
        setPendingSentIds((prev) => new Set([...prev, targetUserId]));
        showToast('Connection request is already pending', 'info');
      } else if (msg.toLowerCase().includes('already connected')) {
        setConnectedIds((prev) => new Set([...prev, targetUserId]));
        showToast('Already connected with this student', 'info');
      } else {
        showToast(msg || 'Could not send request', 'error');
      }
    } finally {
      setSendingId(null);
    }
  };

  const renderStudentCard = (student, showMutuals = false) => {
    const studentId = student.user_id || student.id;
    const isSelf = studentId === currentUser?.user_id;
    const isConnected = connectedIds.has(studentId);
    const isPendingSent = pendingSentIds.has(studentId);
    const isPendingReceived = pendingReceivedIds.has(studentId);
    const mutualCount = student.mutual_connections_count || student.mutual_count || 0;

    return (
      <article
        key={studentId}
        className="bg-white rounded-xl border border-soft-sand/80 p-4 sm:p-5 shadow-[0_1px_3px_0_rgba(39,40,56,0.03)] hover:border-soft-sand hover:shadow-subtle transition-all duration-150 flex flex-col justify-between"
      >
        <div className="flex items-start gap-3.5">
          <div
            className="cursor-pointer shrink-0 group"
            onClick={() => onSelectUser && onSelectUser(studentId)}
          >
            <Avatar
              name={student.full_name || student.username}
              size="md"
              className="ring-1 ring-soft-sand/60 transition-transform group-hover:scale-105"
            />
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-baseline justify-between gap-2">
              <h3
                onClick={() => onSelectUser && onSelectUser(studentId)}
                className="text-sm sm:text-[15px] font-sans font-semibold text-shadow-grey hover:text-deep-crimson cursor-pointer transition-colors truncate"
              >
                {student.full_name}
              </h3>
              {isSelf && (
                <span className="text-[10px] uppercase tracking-wider text-iron-grey/70 font-sans font-medium px-1.5 py-0.5 bg-soft-sand/40 rounded border border-soft-sand/60 shrink-0">
                  You
                </span>
              )}
            </div>

            <p className="text-xs text-iron-grey/80 font-sans truncate">
              @{student.username}
            </p>

            <p className="text-xs text-iron-grey font-sans mt-1 truncate">
              {student.programme || student.department || 'Student'}
              {student.academic_year ? (
                <span className="text-iron-grey/70"> &middot; Year {student.academic_year}</span>
              ) : null}
            </p>

            {/* Real Mutual Connections Count */}
            {showMutuals && mutualCount > 0 && (
              <p className="text-[11px] text-deep-crimson font-sans mt-1 flex items-center gap-1 font-medium">
                <span>&bull;</span>
                <span>{mutualCount} mutual connection{mutualCount > 1 ? 's' : ''}</span>
              </p>
            )}

            {student.bio && (
              <p className="text-xs text-iron-grey/90 font-serif line-clamp-2 mt-2 leading-relaxed">
                {student.bio}
              </p>
            )}
          </div>
        </div>

        {/* Footer Action Bar */}
        <div className="flex items-center justify-between pt-3 mt-3.5 border-t border-soft-sand/60 text-xs">
          <button
            type="button"
            onClick={() => onSelectUser && onSelectUser(studentId)}
            className="text-iron-grey/75 hover:text-shadow-grey font-medium font-sans transition-colors"
          >
            View Profile &rarr;
          </button>

          <div>
            {isSelf ? null : isConnected ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-800 bg-emerald-50 border border-emerald-200/80 px-2.5 py-1 rounded-md">
                <svg className="w-3 h-3 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
                </svg>
                Connected
              </span>
            ) : isPendingSent ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-iron-grey bg-soft-sand/50 border border-soft-sand px-2.5 py-1 rounded-md">
                Pending
              </span>
            ) : isPendingReceived ? (
              <span className="inline-flex items-center gap-1 text-[11px] font-medium text-deep-crimson bg-deep-crimson/5 border border-deep-crimson/20 px-2.5 py-1 rounded-md">
                Received Request
              </span>
            ) : (
              <Button
                size="sm"
                variant="primary"
                disabled={sendingId === studentId}
                loading={sendingId === studentId}
                onClick={() => handleSendRequest(studentId)}
                className="font-medium text-xs px-3.5 shadow-subtle"
              >
                Connect
              </Button>
            )}
          </div>
        </div>
      </article>
    );
  };

  return (
    <div className="space-y-6">
      {/* 1. Compact Editorial Header */}
      <header className="pb-3 border-b border-soft-sand/80 flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-1">
        <div>
          <h1 className="text-xl sm:text-2xl font-serif font-bold text-shadow-grey tracking-tight">
            Discover Peers
          </h1>
          <p className="text-xs sm:text-sm text-iron-grey font-sans mt-0.5">
            Explore students across faculties and connect with university colleagues.
          </p>
        </div>
        <div className="hidden sm:flex items-center gap-1.5 text-[11px] font-sans text-iron-grey/80 bg-soft-sand/40 px-2.5 py-1 rounded-full border border-soft-sand/60 shrink-0">
          <span className="w-1.5 h-1.5 rounded-full bg-deep-crimson inline-block"></span>
          <span>Trie Prefix Engine</span>
        </div>
      </header>

      {/* 2. Primary Search Input Box */}
      <section aria-label="Student search" className="bg-white rounded-xl border border-soft-sand/90 shadow-subtle p-3.5 sm:p-4 focus-within:border-iron-grey/40 focus-within:shadow-card transition-all duration-200">
        <div className="relative flex items-center">
          <svg
            className="w-4 h-4 text-iron-grey/50 absolute left-3.5 pointer-events-none"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <label htmlFor="student-prefix-search" className="sr-only">
            Search students by name, surname, or username prefix
          </label>
          <input
            id="student-prefix-search"
            name="query"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search students by name, surname, or username prefix (e.g. 'aar', 'pri', 'sharma')..."
            className="w-full bg-warm-porcelain/40 focus:bg-white text-sm sm:text-[15px] text-shadow-grey placeholder:text-iron-grey/50 rounded-lg pl-10 pr-9 py-2.5 border border-soft-sand/80 focus:border-iron-grey/40 focus:outline-none focus:ring-1 focus:ring-iron-grey/25 transition-all font-sans"
            autoFocus
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="absolute right-3 text-iron-grey/50 hover:text-shadow-grey p-1 rounded transition-colors text-xs"
              title="Clear search"
            >
              ✕
            </button>
          )}
        </div>

        {/* Live Search Status Bar */}
        <div className="flex items-center justify-between mt-2.5 px-1 text-[11px] text-iron-grey/70 font-sans">
          <span>
            {query.trim()
              ? loading
                ? 'Searching prefix index...'
                : `${results.length} student${results.length === 1 ? '' : 's'} found`
              : 'Indexed in-memory Trie: instant lookup across names & usernames'}
          </span>
          {!query.trim() && (
            <span className="hidden sm:inline text-iron-grey/60">
              Type 1 or more characters to match
            </span>
          )}
        </div>
      </section>

      {/* 3. Results Section */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4" aria-label="Loading students">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-soft-sand/70 p-4 sm:p-5 space-y-3 animate-pulse"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-soft-sand/70 shrink-0"></div>
                <div className="space-y-1.5 flex-1 min-w-0">
                  <div className="h-3.5 bg-soft-sand/70 rounded w-28"></div>
                  <div className="h-2.5 bg-soft-sand/40 rounded w-20"></div>
                </div>
              </div>
              <div className="space-y-1.5 pt-1">
                <div className="h-3 bg-soft-sand/50 rounded w-36"></div>
              </div>
            </div>
          ))}
        </div>
      ) : query.trim() && results.length === 0 ? (
        /* No Results State */
        <div className="bg-white/80 border border-soft-sand rounded-xl p-8 sm:p-10 text-center shadow-subtle">
          <div className="w-10 h-10 mx-auto mb-3 rounded-full bg-soft-sand/40 border border-soft-sand/70 flex items-center justify-center text-iron-grey text-sm font-serif">
            &empty;
          </div>
          <h2 className="text-base font-serif font-bold text-shadow-grey mb-1">
            No students found
          </h2>
          <p className="text-xs sm:text-sm text-iron-grey max-w-sm mx-auto leading-relaxed font-sans">
            No registered profile matches the prefix &ldquo;<span className="font-semibold text-shadow-grey">{query}</span>&rdquo;. Check spelling or try a shorter prefix.
          </p>
        </div>
      ) : query.trim() ? (
        /* Active Search Results Grid */
        <div className="space-y-3">
          <div className="flex items-center justify-between text-xs font-sans text-iron-grey px-0.5">
            <span className="font-semibold text-shadow-grey uppercase tracking-wider text-[11px]">
              Search Matches
            </span>
            <span>{results.length} record{results.length === 1 ? '' : 's'}</span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.map((student) => renderStudentCard(student, false))}
          </div>
        </div>
      ) : (
        /* Initial Discover State (When search is empty) */
        <div className="space-y-6">
          {/* Graph Recommendations Section (backed by real 2-hop mutuals) */}
          {recommendations.length > 0 && (
            <section aria-label="Recommended connections" className="space-y-3">
              <div className="flex items-baseline justify-between text-xs font-sans text-iron-grey px-0.5">
                <div>
                  <h2 className="font-serif font-bold text-base text-shadow-grey">
                    Students in Your Network
                  </h2>
                  <p className="text-[11px] text-iron-grey/80 mt-0.5">
                    Peer suggestions derived from graph neighborhood and mutual connections.
                  </p>
                </div>
                <span className="text-[11px] text-iron-grey/70 font-sans hidden sm:inline">
                  {recommendations.length} suggestion{recommendations.length === 1 ? '' : 's'}
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {recommendations.map((student) => renderStudentCard(student, true))}
              </div>
            </section>
          )}

          {/* Academic Search Guidance Banner */}
          <div className="bg-white/70 border border-soft-sand rounded-xl p-6 sm:p-7 text-center shadow-subtle space-y-2.5">
            <div className="w-10 h-10 mx-auto rounded-full bg-soft-sand/50 border border-soft-sand/70 flex items-center justify-center text-iron-grey">
              <svg className="w-5 h-5 text-iron-grey" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.7" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h3 className="text-base font-serif font-bold text-shadow-grey">
              Explore the Campus Community
            </h3>
            <p className="text-xs sm:text-sm text-iron-grey max-w-md mx-auto leading-relaxed font-sans">
              Search by name prefix or username above to discover classmates across programs, examine mutual connections, and expand your academic circle.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
