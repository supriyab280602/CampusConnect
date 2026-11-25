import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { api } from '../../services/api';
import { Button } from '../common/Button';
import { Avatar } from '../common/Avatar';

export function NetworkView({ onSelectUser }) {
  const { currentUser } = useAuth();
  const { showToast } = useToast();

  // Overview metrics
  const [degree, setDegree] = useState(0);
  const [connectionCount, setConnectionCount] = useState(0);
  const [recommendations, setRecommendations] = useState([]);
  const [loadingRecs, setLoadingRecs] = useState(true);

  // BFS Shortest Path Explorer State
  const [targetIdInput, setTargetIdInput] = useState('');
  const [pathResult, setPathResult] = useState(null);
  const [pathError, setPathError] = useState(null);
  const [searchingPath, setSearchingPath] = useState(false);
  const [searchedTargetName, setSearchedTargetName] = useState('');

  // Mutuals / Connection Analysis State
  const [inspectingUser, setInspectingUser] = useState(null);
  const [mutualsResult, setMutualsResult] = useState(null);
  const [targetDegree, setTargetDegree] = useState(null);
  const [loadingMutuals, setLoadingMutuals] = useState(false);

  // Relationship tracking for recommendations
  const [connectedIds, setConnectedIds] = useState(new Set());
  const [pendingSentIds, setPendingSentIds] = useState(new Set());
  const [sendingId, setSendingId] = useState(null);

  const loadNetworkData = useCallback(async () => {
    try {
      setLoadingRecs(true);
      const [recRes, degRes, connRes, sentRes] = await Promise.allSettled([
        api.get('/network/recommendations?limit=8'),
        api.get(`/network/${currentUser?.user_id}/degree`),
        api.get('/connections'),
        api.get('/connections/requests/sent'),
      ]);

      if (recRes.status === 'fulfilled' && recRes.value?.success) {
        setRecommendations(recRes.value.data?.recommendations || []);
      }
      if (degRes.status === 'fulfilled' && degRes.value?.success && typeof degRes.value.data?.degree === 'number') {
        setDegree(degRes.value.data.degree);
      }
      if (connRes.status === 'fulfilled' && connRes.value?.success) {
        const conns = connRes.value.data?.connections || [];
        setConnectionCount(conns.length);
        const set = new Set(conns.map((c) => c.user_id || c.id || c.user?.user_id).filter(Boolean));
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
    } catch (err) {
      showToast(err.message || 'Failed to load network intelligence', 'error');
    } finally {
      setLoadingRecs(false);
    }
  }, [currentUser?.user_id, showToast]);

  useEffect(() => {
    if (currentUser?.user_id) {
      loadNetworkData();
    }
  }, [currentUser?.user_id, loadNetworkData]);

  // BFS Pathfinding execution
  const handleFindPath = async (e, overrideTargetId, overrideTargetName) => {
    if (e) e.preventDefault();
    const targetToUse = (overrideTargetId || targetIdInput || '').trim();
    if (!targetToUse) return;

    try {
      setSearchingPath(true);
      setPathResult(null);
      setPathError(null);
      setSearchedTargetName(overrideTargetName || targetToUse);
      const res = await api.get(`/network/path?targetUserId=${encodeURIComponent(targetToUse)}`);
      if (res?.success) {
        setPathResult(res.data);
      }
    } catch (err) {
      if (err.status === 404 || err.data?.error?.code === 'RESOURCE_NOT_FOUND') {
        setPathError({
          type: 'not_found',
          message: err.message || `Student '${targetToUse}' not found in directory.`,
        });
      } else {
        showToast(err.message || 'BFS traversal failed', 'error');
      }
    } finally {
      setSearchingPath(false);
    }
  };

  // Inspect mutual connections and degree for a student
  const handleInspectStudent = async (student) => {
    const studentId = student.user_id || student.id;
    try {
      setInspectingUser(student);
      setLoadingMutuals(true);
      setMutualsResult(null);
      setTargetDegree(null);

      const [mutualsRes, degreeRes] = await Promise.allSettled([
        api.get(`/network/${studentId}/mutuals`),
        api.get(`/network/${studentId}/degree`),
      ]);

      if (mutualsRes.status === 'fulfilled' && mutualsRes.value?.success) {
        setMutualsResult(mutualsRes.value.data?.mutual_connections || []);
      }
      if (degreeRes.status === 'fulfilled' && degreeRes.value?.success && typeof degreeRes.value.data?.degree === 'number') {
        setTargetDegree(degreeRes.value.data.degree);
      }
    } catch (err) {
      showToast(err.message || 'Failed to inspect connection details', 'error');
    } finally {
      setLoadingMutuals(false);
    }
  };

  // Send connection request from recommendations
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
        showToast('Connection request already pending', 'info');
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

  return (
    <div className="space-y-6">
      {/* 1. Editorial Page Header */}
      <header className="pb-3 border-b border-soft-sand/80 flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-1">
        <div>
          <h1 className="text-xl sm:text-2xl font-serif font-bold text-shadow-grey tracking-tight">
            Graph Network Intelligence
          </h1>
          <p className="text-xs sm:text-sm text-iron-grey font-sans mt-0.5">
            Topological analysis, mutual cluster inspection, and unweighted BFS shortest paths.
          </p>
        </div>
        <div className="hidden sm:flex items-center gap-1.5 text-[11px] font-sans text-iron-grey/80 bg-soft-sand/40 px-2.5 py-1 rounded-full border border-soft-sand/60 shrink-0">
          <span className="w-1.5 h-1.5 rounded-full bg-deep-crimson inline-block animate-pulse"></span>
          <span>Adjacency-List BFS Engine</span>
        </div>
      </header>

      {/* 2. Graph Metrics Overview Bar */}
      <section aria-label="Network topological summary" className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="bg-white rounded-xl border border-soft-sand/80 p-4 shadow-subtle">
          <span className="text-[11px] font-sans text-iron-grey/80 uppercase tracking-wider block">
            Vertex Degree
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-serif font-bold text-shadow-grey tabular-nums">{degree}</span>
            <span className="text-xs text-iron-grey font-sans">direct graph edges</span>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-soft-sand/80 p-4 shadow-subtle">
          <span className="text-[11px] font-sans text-iron-grey/80 uppercase tracking-wider block">
            Verified Relationships
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-serif font-bold text-shadow-grey tabular-nums">{connectionCount}</span>
            <span className="text-xs text-iron-grey font-sans">accepted connections</span>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-soft-sand/80 p-4 shadow-subtle">
          <span className="text-[11px] font-sans text-iron-grey/80 uppercase tracking-wider block">
            2-Hop Cluster Density
          </span>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-2xl font-serif font-bold text-shadow-grey tabular-nums">{recommendations.length}</span>
            <span className="text-xs text-iron-grey font-sans">candidates recommended</span>
          </div>
        </div>
      </section>

      {/* 3. Centerpiece: BFS Shortest Path Explorer */}
      <section aria-label="BFS Shortest Path Explorer" className="bg-white rounded-xl border border-soft-sand/90 shadow-subtle p-5 sm:p-6 focus-within:border-iron-grey/40 focus-within:shadow-card transition-all duration-200 space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 border-b border-soft-sand/60 pb-3">
          <div>
            <h2 className="text-base sm:text-lg font-serif font-bold text-shadow-grey">
              BFS Shortest Path Explorer
            </h2>
            <p className="text-xs text-iron-grey font-sans mt-0.5">
              Traverse the unweighted student graph via Breadth-First Search to calculate exact degrees of separation.
            </p>
          </div>
          <span className="text-[11px] font-mono text-iron-grey/70 bg-warm-porcelain px-2.5 py-1 rounded border border-soft-sand/60 self-start sm:self-auto">
            O(V + E) Traversal
          </span>
        </div>

        {/* Path Search Form */}
        <form onSubmit={(e) => handleFindPath(e)} className="flex flex-col sm:flex-row gap-2.5">
          <div className="relative flex-1">
            <label htmlFor="network-bfs-target" className="sr-only">
              Student username, full name, or ID
            </label>
            <input
              id="network-bfs-target"
              name="targetUserId"
              type="text"
              value={targetIdInput}
              onChange={(e) => {
                setTargetIdInput(e.target.value);
                if (pathError) setPathError(null);
              }}
              placeholder="Enter student username, full name, or user ID (e.g. 'aarav', 'rohan')..."
              className="w-full bg-warm-porcelain/40 focus:bg-white text-sm sm:text-[15px] text-shadow-grey placeholder:text-iron-grey/50 rounded-lg px-3.5 py-2.5 border border-soft-sand/80 focus:border-iron-grey/40 focus:outline-none focus:ring-1 focus:ring-iron-grey/25 transition-all font-sans"
            />
            {targetIdInput && (
              <button
                type="button"
                onClick={() => {
                  setTargetIdInput('');
                  setPathResult(null);
                  setPathError(null);
                }}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-iron-grey/50 hover:text-shadow-grey p-1 text-xs"
                title="Clear input"
              >
                ✕
              </button>
            )}
          </div>
          <Button
            type="submit"
            variant="primary"
            disabled={!targetIdInput.trim() || searchingPath}
            loading={searchingPath}
            className="font-medium text-xs sm:text-sm px-5 shrink-0"
          >
            Calculate Path
          </Button>
        </form>

        {/* Quick select peer hints if recommendations exist */}
        {(() => {
          const quickCandidates = recommendations.slice(0, 4);
          if (quickCandidates.length === 0 || pathResult || pathError) return null;

          // Detect duplicate display names in currently displayed Quick Trace candidates (CC-QA-003)
          const nameCounts = quickCandidates.reduce((acc, rec) => {
            const student = rec.user || rec;
            const displayName = student.full_name || student.username;
            acc[displayName] = (acc[displayName] || 0) + 1;
            return acc;
          }, {});

          return (
            <div className="flex flex-wrap items-center gap-1.5 text-xs text-iron-grey/80 pt-1">
              <span className="text-[11px] font-sans text-iron-grey/60 mr-1">Quick Trace:</span>
              {quickCandidates.map((rec) => {
                const student = rec.user || rec;
                const baseName = student.full_name || student.username;
                const isDuplicate = nameCounts[baseName] > 1;
                const label = isDuplicate && student.username
                  ? `${baseName} (@${student.username})`
                  : baseName;

                return (
                  <button
                    key={student.user_id || student.id}
                    type="button"
                    onClick={() => {
                      setTargetIdInput(student.username || student.user_id);
                      handleFindPath(null, student.user_id || student.username, label);
                    }}
                    className="inline-flex items-center gap-1 text-[11px] bg-warm-porcelain hover:bg-soft-sand/60 text-shadow-grey px-2.5 py-1 rounded-md border border-soft-sand transition-colors font-sans"
                  >
                    <span>{label}</span>
                    <span className="text-iron-grey/60">&rarr;</span>
                  </button>
                );
              })}
            </div>
          );
        })()}

        {/* Path Results Visualizer */}
        {searchingPath ? (
          <div className="p-6 bg-warm-porcelain/30 rounded-lg border border-soft-sand/60 text-center space-y-2 animate-pulse">
            <p className="text-xs font-sans text-iron-grey">
              Traversing graph adjacency lists and tracking visited vertices...
            </p>
          </div>
        ) : pathError ? (
          <div className="bg-warm-porcelain/40 rounded-xl border border-soft-sand/90 p-4 sm:p-5 space-y-2">
            <div className="flex items-center gap-2 pb-2 border-b border-soft-sand/70 text-xs font-sans">
              <span className="text-iron-grey font-medium">Lookup Status:</span>
              <span className="inline-flex items-center gap-1.5 font-semibold text-deep-crimson">
                <span className="w-2 h-2 rounded-full bg-deep-crimson"></span>
                <span>Student Not Found</span>
              </span>
            </div>
            <div className="p-4 bg-white/80 rounded-lg border border-soft-sand text-center space-y-1">
              <p className="text-xs sm:text-sm font-serif font-semibold text-shadow-grey">
                No student registered as &ldquo;{searchedTargetName}&rdquo;
              </p>
              <p className="text-xs text-iron-grey font-sans leading-relaxed">
                Please verify the student&apos;s username or name and try searching again.
              </p>
            </div>
          </div>
        ) : pathResult ? (
          (() => {
            const isConnected =
              typeof pathResult.distance === 'number' &&
              pathResult.distance >= 0 &&
              Array.isArray(pathResult.path) &&
              pathResult.path.length > 0;

            return (
              <div className="bg-warm-porcelain/40 rounded-xl border border-soft-sand/90 p-4 sm:p-5 space-y-4">
                {/* Metric Status Header */}
                <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-soft-sand/70 text-xs font-sans">
                  <div className="flex items-center gap-2">
                    <span className="text-iron-grey font-medium">Degree of Separation:</span>
                    <span
                      className={`px-2.5 py-0.5 rounded font-semibold tabular-nums text-xs ${
                        isConnected
                          ? 'bg-deep-crimson/10 text-deep-crimson border border-deep-crimson/20'
                          : 'bg-soft-sand text-iron-grey'
                      }`}
                    >
                      {isConnected
                        ? `${pathResult.distance} Hop${pathResult.distance === 1 ? '' : 's'}`
                        : 'Disconnected'}
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-iron-grey font-medium">Topology Status:</span>
                    <span className="flex items-center gap-1.5 font-medium text-shadow-grey">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          isConnected ? 'bg-emerald-600' : 'bg-iron-grey/50'
                        }`}
                      ></span>
                      <span>{isConnected ? 'Connected Component' : 'No Path Found'}</span>
                    </span>
                  </div>
                </div>

                {/* Path Node Sequence or Disconnected Notice */}
                {isConnected ? (
                  <div className="space-y-3 pt-1">
                    <span className="text-[11px] font-sans font-semibold text-iron-grey uppercase tracking-wider block">
                      Shortest Traversal Sequence ({pathResult.path.length} vertices)
                    </span>

                    {/* Responsive Visual Node Chain */}
                    <div className="flex flex-col sm:flex-row sm:flex-wrap sm:items-center gap-2.5 sm:gap-2">
                      {pathResult.path.map((node, index) => {
                        const nodeId = typeof node === 'string' ? node : node.id || node.user_id;
                        const isFirst = index === 0;
                        const isLast = index === pathResult.path.length - 1;
                        const isCurrentUser = nodeId === currentUser?.user_id;

                        const nodeName = isCurrentUser
                          ? 'You'
                          : typeof node === 'object'
                          ? node.full_name || node.username || 'Student'
                          : nodeId;

                        return (
                          <React.Fragment key={nodeId}>
                            <div
                              onClick={() => onSelectUser && onSelectUser(nodeId)}
                              className={`flex items-center gap-2.5 bg-white px-3.5 py-2 rounded-lg border transition-all cursor-pointer group shadow-subtle ${
                                isFirst
                                  ? 'border-deep-crimson/40 bg-deep-crimson/5'
                                  : isLast
                                  ? 'border-emerald-500/50 hover:border-emerald-600'
                                  : 'border-soft-sand hover:border-iron-grey/40'
                              }`}
                            >
                              <Avatar name={nodeName} size="sm" className="shrink-0" />
                              <div className="min-w-0">
                                <span className="text-xs font-semibold font-sans text-shadow-grey group-hover:text-deep-crimson transition-colors block truncate">
                                  {nodeName}
                                </span>
                                <span className="text-[10px] text-iron-grey font-sans block truncate">
                                  {isFirst ? 'Source Node' : isLast ? 'Target Node' : `Hop ${index}`}
                                </span>
                              </div>
                            </div>

                            {!isLast && (
                              <div className="flex sm:inline-flex items-center justify-center my-0.5 sm:my-0 text-iron-grey px-1">
                                <svg
                                  className="w-4 h-4 hidden sm:inline text-iron-grey/60"
                                  fill="none"
                                  viewBox="0 0 24 24"
                                  stroke="currentColor"
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                                </svg>
                                <svg
                                  className="w-4 h-4 sm:hidden text-iron-grey/60"
                                  fill="none"
                                  viewBox="0 0 24 24"
                                  stroke="currentColor"
                                >
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                                </svg>
                              </div>
                            )}
                          </React.Fragment>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-white/80 rounded-lg border border-soft-sand text-center space-y-1">
                    <p className="text-xs sm:text-sm font-serif font-semibold text-shadow-grey">
                      No path found to &ldquo;{searchedTargetName}&rdquo;
                    </p>
                    <p className="text-xs text-iron-grey font-sans leading-relaxed">
                      These two vertices belong to disconnected graph components. An edge will form once an intermediate connection is accepted.
                    </p>
                  </div>
                )}
              </div>
            );
          })()
        ) : null}
      </section>

      {/* 4. Mutual Connections & Inspection Section */}
      {inspectingUser && (
        <section aria-label="Mutual connection inspector" className="bg-white rounded-xl border border-soft-sand/90 p-5 shadow-subtle space-y-4">
          <div className="flex items-center justify-between border-b border-soft-sand/60 pb-3">
            <div className="flex items-center gap-3 min-w-0">
              <Avatar
                name={inspectingUser.full_name || inspectingUser.username}
                size="md"
                className="shrink-0"
              />
              <div className="min-w-0">
                <h3 className="text-sm sm:text-base font-serif font-bold text-shadow-grey truncate">
                  Mutual Analysis with {inspectingUser.full_name}
                </h3>
                <p className="text-xs text-iron-grey font-sans">
                  @{inspectingUser.username}
                  {targetDegree !== null ? ` · Degree: ${targetDegree} edges` : ''}
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                setInspectingUser(null);
                setMutualsResult(null);
                setTargetDegree(null);
              }}
              className="text-xs text-iron-grey hover:text-shadow-grey p-1.5 font-sans rounded hover:bg-soft-sand/40 transition-colors"
            >
              ✕ Close
            </button>
          </div>

          {loadingMutuals ? (
            <p className="text-xs font-sans text-iron-grey py-3 animate-pulse">
              Computing intersection of adjacency lists...
            </p>
          ) : !mutualsResult || mutualsResult.length === 0 ? (
            <div className="p-4 bg-warm-porcelain/40 rounded-lg border border-soft-sand/70 text-center">
              <p className="text-xs text-iron-grey font-sans">
                No mutual connections exist between you and {inspectingUser.full_name}.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <span className="text-[11px] font-sans text-iron-grey uppercase tracking-wider block">
                {mutualsResult.length} Mutual Peer{mutualsResult.length === 1 ? '' : 's'}:
              </span>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                {mutualsResult.map((m) => {
                  const mId = m.user_id || m.id;
                  return (
                    <div
                      key={mId}
                      className="flex items-center gap-2.5 bg-warm-porcelain/40 hover:bg-white p-2.5 rounded-lg border border-soft-sand transition-all cursor-pointer group"
                      onClick={() => onSelectUser && onSelectUser(mId)}
                    >
                      <Avatar name={m.full_name || m.username} size="sm" className="shrink-0" />
                      <div className="min-w-0">
                        <span className="text-xs font-semibold text-shadow-grey group-hover:text-deep-crimson transition-colors block truncate font-sans">
                          {m.full_name || m.username}
                        </span>
                        <span className="text-[10px] text-iron-grey block truncate font-sans">
                          @{m.username}
                        </span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </section>
      )}

      {/* 5. 2-Hop Graph Recommendations */}
      <section aria-label="Network recommendations" className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-1 border-b border-soft-sand/70 pb-2">
          <div>
            <h2 className="font-serif font-bold text-base text-shadow-grey">
              2-Hop Network Recommendations
            </h2>
            <p className="text-[11px] text-iron-grey font-sans mt-0.5">
              Peers exactly two steps away in the university graph, ranked by common mutual edges.
            </p>
          </div>
          <span className="text-[11px] font-sans text-iron-grey/70 hidden sm:inline">
            Ranked by mutual friend density
          </span>
        </div>

        {loadingRecs ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[1, 2].map((i) => (
              <div key={i} className="bg-white rounded-xl border border-soft-sand/70 p-4 space-y-3 animate-pulse">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-soft-sand/70"></div>
                  <div className="space-y-1.5 flex-1">
                    <div className="h-3.5 bg-soft-sand/70 rounded w-28"></div>
                    <div className="h-2.5 bg-soft-sand/40 rounded w-20"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : recommendations.length === 0 ? (
          <div className="bg-white/80 border border-soft-sand rounded-xl p-8 text-center shadow-subtle">
            <h3 className="text-base font-serif font-bold text-shadow-grey mb-1">
              No 2-hop candidates available
            </h3>
            <p className="text-xs text-iron-grey max-w-sm mx-auto leading-relaxed font-sans">
              As your direct connections accept more peers, candidates with mutual ties will automatically appear here.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {recommendations.map((rec) => {
              const student = rec.user || rec;
              const studentId = student.user_id || student.id;
              const mutualCount = rec.mutual_count ?? rec.mutual_connections_count ?? 0;
              const isConnected = connectedIds.has(studentId);
              const isPending = pendingSentIds.has(studentId);

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
                      <h3
                        onClick={() => onSelectUser && onSelectUser(studentId)}
                        className="text-sm sm:text-[15px] font-sans font-semibold text-shadow-grey hover:text-deep-crimson cursor-pointer transition-colors truncate"
                      >
                        {student.full_name}
                      </h3>
                      <p className="text-xs text-iron-grey/80 font-sans truncate">
                        @{student.username}
                      </p>

                      <p className="text-xs text-iron-grey font-sans mt-1 truncate">
                        {student.programme || student.department || 'Student'}
                        {student.academic_year ? ` · Year ${student.academic_year}` : ''}
                      </p>

                      {mutualCount > 0 && (
                        <p className="text-[11px] text-deep-crimson font-sans mt-1 flex items-center gap-1 font-medium">
                          <span>&bull;</span>
                          <span>{mutualCount} mutual connection{mutualCount !== 1 ? 's' : ''}</span>
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Graph Analysis & Connect Action Row */}
                  <div className="flex items-center justify-between pt-3 mt-3.5 border-t border-soft-sand/60 text-xs font-sans">
                    <div className="flex items-center gap-3">
                      <button
                        type="button"
                        onClick={() => handleInspectStudent(student)}
                        className="text-xs font-medium text-iron-grey hover:text-shadow-grey hover:underline transition-colors"
                      >
                        Mutuals
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          setTargetIdInput(student.username || studentId);
                          handleFindPath(null, studentId, student.full_name || student.username);
                        }}
                        className="text-xs font-medium text-iron-grey hover:text-deep-crimson transition-colors"
                      >
                        Trace BFS &rarr;
                      </button>
                    </div>

                    <div>
                      {isConnected ? (
                        <span className="text-[11px] font-medium text-emerald-800 bg-emerald-50 border border-emerald-200/80 px-2.5 py-1 rounded-md">
                          Connected
                        </span>
                      ) : isPending ? (
                        <span className="text-[11px] font-medium text-iron-grey bg-soft-sand/50 border border-soft-sand px-2.5 py-1 rounded-md">
                          Pending
                        </span>
                      ) : (
                        <Button
                          size="sm"
                          variant="primary"
                          disabled={sendingId === studentId}
                          loading={sendingId === studentId}
                          onClick={() => handleSendRequest(studentId)}
                          className="font-medium text-xs px-3 shadow-subtle"
                        >
                          Connect
                        </Button>
                      )}
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}
