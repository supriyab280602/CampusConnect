import React, { useState, useEffect, useCallback } from 'react';
import { useToast } from '../../context/ToastContext';
import { api } from '../../services/api';
import { Button } from '../common/Button';
import { Avatar } from '../common/Avatar';

export function ConnectionsView({ onSelectUser }) {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState('connections'); // 'connections' | 'received' | 'sent'
  const [connections, setConnections] = useState([]);
  const [receivedRequests, setReceivedRequests] = useState([]);
  const [sentRequests, setSentRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoadingId, setActionLoadingId] = useState(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [connsRes, recvRes, sentRes] = await Promise.all([
        api.get('/connections'),
        api.get('/connections/requests/received'),
        api.get('/connections/requests/sent'),
      ]);

      if (connsRes?.success) setConnections(connsRes.data.connections || []);
      if (recvRes?.success) setReceivedRequests(recvRes.data.requests || []);
      if (sentRes?.success) setSentRequests(sentRes.data.requests || []);
    } catch (err) {
      showToast(err.message || 'Failed to load connections data', 'error');
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleAccept = async (requestId) => {
    try {
      setActionLoadingId(requestId);
      await api.post(`/connections/requests/${requestId}/accept`);
      showToast('Connection request accepted');
      await loadData();
    } catch (err) {
      showToast(err.message || 'Could not accept request', 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleReject = async (requestId) => {
    try {
      setActionLoadingId(requestId);
      await api.post(`/connections/requests/${requestId}/reject`);
      showToast('Connection request declined');
      await loadData();
    } catch (err) {
      showToast(err.message || 'Could not decline request', 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleCancel = async (requestId) => {
    try {
      setActionLoadingId(requestId);
      await api.post(`/connections/requests/${requestId}/cancel`);
      showToast('Pending request cancelled');
      await loadData();
    } catch (err) {
      showToast(err.message || 'Could not cancel request', 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  const handleRemoveConnection = async (partnerUserId, partnerName) => {
    if (!window.confirm(`Are you sure you want to remove ${partnerName || 'this student'} from your connections?`)) {
      return;
    }
    try {
      setActionLoadingId(partnerUserId);
      await api.delete(`/connections/${partnerUserId}`);
      showToast('Connection removed from network');
      await loadData();
    } catch (err) {
      showToast(err.message || 'Could not remove connection', 'error');
    } finally {
      setActionLoadingId(null);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Page Header */}
      <header className="pb-3 border-b border-soft-sand/80 flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-1">
        <div>
          <h1 className="text-xl sm:text-2xl font-serif font-bold text-shadow-grey tracking-tight">
            Academic Connections
          </h1>
          <p className="text-xs sm:text-sm text-iron-grey font-sans mt-0.5">
            Manage confirmed collegiate ties and incoming peer invitations.
          </p>
        </div>
        <div className="hidden sm:flex items-center gap-1.5 text-[11px] font-sans text-iron-grey/80 bg-soft-sand/40 px-2.5 py-1 rounded-full border border-soft-sand/60 shrink-0">
          <span className="w-1.5 h-1.5 rounded-full bg-deep-crimson inline-block"></span>
          <span>Relationship Directory</span>
        </div>
      </header>

      {/* 2. Management Tab Navigation */}
      <nav aria-label="Connection categories" className="flex border-b border-soft-sand/70 gap-2 sm:gap-6 text-sm font-sans">
        <button
          type="button"
          onClick={() => setActiveTab('connections')}
          className={`pb-2.5 font-medium transition-colors relative flex items-center gap-2 ${
            activeTab === 'connections'
              ? 'text-deep-crimson font-semibold border-b-2 border-deep-crimson -mb-px'
              : 'text-iron-grey/80 hover:text-shadow-grey'
          }`}
        >
          <span>My Connections</span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full tabular-nums font-sans ${
              activeTab === 'connections'
                ? 'bg-deep-crimson/10 text-deep-crimson font-semibold'
                : 'bg-soft-sand/60 text-iron-grey'
            }`}
          >
            {connections.length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('received')}
          className={`pb-2.5 font-medium transition-colors relative flex items-center gap-2 ${
            activeTab === 'received'
              ? 'text-deep-crimson font-semibold border-b-2 border-deep-crimson -mb-px'
              : 'text-iron-grey/80 hover:text-shadow-grey'
          }`}
        >
          <span>Requests Received</span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full tabular-nums font-sans ${
              receivedRequests.length > 0
                ? 'bg-deep-crimson text-white font-bold'
                : activeTab === 'received'
                ? 'bg-deep-crimson/10 text-deep-crimson font-semibold'
                : 'bg-soft-sand/60 text-iron-grey'
            }`}
          >
            {receivedRequests.length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('sent')}
          className={`pb-2.5 font-medium transition-colors relative flex items-center gap-2 ${
            activeTab === 'sent'
              ? 'text-deep-crimson font-semibold border-b-2 border-deep-crimson -mb-px'
              : 'text-iron-grey/80 hover:text-shadow-grey'
          }`}
        >
          <span>Sent Requests</span>
          <span
            className={`text-xs px-2 py-0.5 rounded-full tabular-nums font-sans ${
              activeTab === 'sent'
                ? 'bg-deep-crimson/10 text-deep-crimson font-semibold'
                : 'bg-soft-sand/60 text-iron-grey'
            }`}
          >
            {sentRequests.length}
          </span>
        </button>
      </nav>

      {/* 3. Section Content */}
      {loading ? (
        <div className="space-y-3" aria-label="Loading connection records">
          {[1, 2, 3].map((i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-soft-sand/70 p-4 sm:p-5 flex items-center justify-between gap-4 animate-pulse"
            >
              <div className="flex items-center gap-3.5 min-w-0">
                <div className="w-10 h-10 rounded-full bg-soft-sand/70 shrink-0"></div>
                <div className="space-y-1.5">
                  <div className="h-3.5 bg-soft-sand/70 rounded w-32"></div>
                  <div className="h-2.5 bg-soft-sand/40 rounded w-24"></div>
                </div>
              </div>
              <div className="h-8 bg-soft-sand/40 rounded w-20 shrink-0"></div>
            </div>
          ))}
        </div>
      ) : activeTab === 'connections' ? (
        /* SECTION: My Connections (Scannable relationship list) */
        connections.length === 0 ? (
          <div className="bg-white/80 border border-soft-sand rounded-xl p-8 sm:p-12 text-center shadow-subtle">
            <div className="w-11 h-11 mx-auto mb-3 rounded-full bg-soft-sand/50 border border-soft-sand/70 flex items-center justify-center text-iron-grey">
              <svg className="w-5 h-5 text-iron-grey" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
            <h2 className="text-base sm:text-lg font-serif font-bold text-shadow-grey mb-1">
              No campus connections yet
            </h2>
            <p className="text-xs sm:text-sm text-iron-grey max-w-sm mx-auto leading-relaxed font-sans mb-4">
              You haven't formed any confirmed student relationships yet. Discover classmates and faculty colleagues to begin expanding your circle.
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-soft-sand/80 shadow-subtle divide-y divide-soft-sand/60 overflow-hidden">
            {connections.map((conn) => {
              const partner = conn.user || conn;
              const partnerId = partner.user_id || partner.id || conn.user_id;
              const partnerName = partner.full_name || partner.username || 'Student';

              return (
                <div
                  key={conn.connection_id || partnerId}
                  className="p-4 sm:p-4.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3.5 hover:bg-warm-porcelain/30 transition-colors"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div
                      className="cursor-pointer shrink-0 group"
                      onClick={() => onSelectUser && onSelectUser(partnerId)}
                    >
                      <Avatar
                        name={partnerName}
                        size="md"
                        className="ring-1 ring-soft-sand/60 transition-transform group-hover:scale-105"
                      />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-baseline gap-2">
                        <h3
                          onClick={() => onSelectUser && onSelectUser(partnerId)}
                          className="text-sm sm:text-[15px] font-sans font-semibold text-shadow-grey hover:text-deep-crimson cursor-pointer transition-colors truncate"
                        >
                          {partnerName}
                        </h3>
                        <span className="text-xs text-iron-grey/75 font-sans truncate">
                          @{partner.username}
                        </span>
                      </div>
                      <p className="text-xs text-iron-grey font-sans mt-0.5 truncate">
                        {partner.programme || partner.department || 'Student'}
                        {partner.academic_year ? (
                          <span className="text-iron-grey/70"> &middot; Year {partner.academic_year}</span>
                        ) : null}
                        {conn.created_at && (
                          <span className="text-iron-grey/60 hidden md:inline">
                            {' '}&middot; Connected {formatDate(conn.created_at)}
                          </span>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-2 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-soft-sand/40">
                    <button
                      type="button"
                      onClick={() => onSelectUser && onSelectUser(partnerId)}
                      className="text-xs font-sans font-medium text-iron-grey hover:text-shadow-grey px-2.5 py-1.5 rounded transition-colors"
                    >
                      View Profile &rarr;
                    </button>
                    <button
                      type="button"
                      disabled={actionLoadingId === partnerId}
                      onClick={() => handleRemoveConnection(partnerId, partnerName)}
                      className="text-xs font-sans text-iron-grey/60 hover:text-deep-crimson hover:bg-soft-sand/40 px-2.5 py-1.5 rounded transition-colors disabled:opacity-50"
                      title="Remove connection"
                    >
                      {actionLoadingId === partnerId ? 'Removing...' : 'Remove'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )
      ) : activeTab === 'received' ? (
        /* SECTION: Requests Received (Actionable incoming invitations) */
        receivedRequests.length === 0 ? (
          <div className="bg-white/80 border border-soft-sand rounded-xl p-8 sm:p-12 text-center shadow-subtle">
            <div className="w-11 h-11 mx-auto mb-3 rounded-full bg-soft-sand/50 border border-soft-sand/70 flex items-center justify-center text-iron-grey">
              <svg className="w-5 h-5 text-iron-grey" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            </div>
            <h2 className="text-base sm:text-lg font-serif font-bold text-shadow-grey mb-1">
              No pending invitations
            </h2>
            <p className="text-xs sm:text-sm text-iron-grey max-w-sm mx-auto leading-relaxed font-sans">
              You have reviewed all incoming connection requests. When new invitations arrive, you can accept or decline them here.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {receivedRequests.map((req) => {
              const reqId = req.request_id || req.id;
              const sender = req.sender || { username: req.sender_id, full_name: req.sender_id };
              const senderId = sender.user_id || req.sender_id;
              const senderName = sender.full_name || sender.username || 'Student';

              return (
                <div
                  key={reqId}
                  className="bg-white rounded-xl border border-soft-sand/80 p-4 sm:p-5 shadow-[0_1px_3px_0_rgba(39,40,56,0.03)] flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div
                      className="cursor-pointer shrink-0 group"
                      onClick={() => onSelectUser && onSelectUser(senderId)}
                    >
                      <Avatar
                        name={senderName}
                        size="md"
                        className="ring-1 ring-soft-sand/60 transition-transform group-hover:scale-105"
                      />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-baseline gap-2">
                        <h3
                          onClick={() => onSelectUser && onSelectUser(senderId)}
                          className="text-sm sm:text-[15px] font-sans font-semibold text-shadow-grey hover:text-deep-crimson cursor-pointer transition-colors truncate"
                        >
                          {senderName}
                        </h3>
                        <span className="text-xs text-iron-grey/75 font-sans truncate">
                          @{sender.username}
                        </span>
                      </div>
                      <p className="text-xs text-iron-grey font-sans mt-0.5 truncate">
                        {sender.programme || sender.department || 'Student'}
                        {sender.academic_year ? ` · Year ${sender.academic_year}` : ''}
                        {' '}&middot; Received {formatDate(req.created_at)}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-soft-sand/40">
                    <Button
                      size="sm"
                      variant="primary"
                      disabled={actionLoadingId === reqId}
                      loading={actionLoadingId === reqId}
                      onClick={() => handleAccept(reqId)}
                      className="font-medium text-xs px-4 shadow-subtle"
                    >
                      Accept
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={actionLoadingId === reqId}
                      onClick={() => handleReject(reqId)}
                      className="font-medium text-xs px-3 hover:text-deep-crimson"
                    >
                      Decline
                    </Button>
                  </div>
                </div>
              );
            })}
          </div>
        )
      ) : (
        /* SECTION: Requests Sent (Outgoing pending invitations) */
        sentRequests.length === 0 ? (
          <div className="bg-white/80 border border-soft-sand rounded-xl p-8 sm:p-12 text-center shadow-subtle">
            <div className="w-11 h-11 mx-auto mb-3 rounded-full bg-soft-sand/50 border border-soft-sand/70 flex items-center justify-center text-iron-grey">
              <svg className="w-5 h-5 text-iron-grey" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </div>
            <h2 className="text-base sm:text-lg font-serif font-bold text-shadow-grey mb-1">
              No outgoing requests
            </h2>
            <p className="text-xs sm:text-sm text-iron-grey max-w-sm mx-auto leading-relaxed font-sans">
              You have no pending invitations awaiting approval. Explore students in Discover to send connection requests.
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-xl border border-soft-sand/80 shadow-subtle divide-y divide-soft-sand/60 overflow-hidden">
            {sentRequests.map((req) => {
              const reqId = req.request_id || req.id;
              const receiver = req.receiver || { username: req.receiver_id, full_name: req.receiver_id };
              const receiverId = receiver.user_id || req.receiver_id;
              const receiverName = receiver.full_name || receiver.username || 'Student';

              return (
                <div
                  key={reqId}
                  className="p-4 sm:p-4.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3.5 hover:bg-warm-porcelain/30 transition-colors"
                >
                  <div className="flex items-center gap-3.5 min-w-0">
                    <div
                      className="cursor-pointer shrink-0 group"
                      onClick={() => onSelectUser && onSelectUser(receiverId)}
                    >
                      <Avatar
                        name={receiverName}
                        size="md"
                        className="ring-1 ring-soft-sand/60 transition-transform group-hover:scale-105"
                      />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-baseline gap-2">
                        <h3
                          onClick={() => onSelectUser && onSelectUser(receiverId)}
                          className="text-sm sm:text-[15px] font-sans font-semibold text-shadow-grey hover:text-deep-crimson cursor-pointer transition-colors truncate"
                        >
                          {receiverName}
                        </h3>
                        <span className="text-xs text-iron-grey/75 font-sans truncate">
                          @{receiver.username}
                        </span>
                      </div>
                      <p className="text-xs text-iron-grey font-sans mt-0.5 truncate">
                        {receiver.programme || receiver.department || 'Student'}
                        {receiver.academic_year ? ` · Year ${receiver.academic_year}` : ''}
                        {' '}&middot; Sent {formatDate(req.created_at)}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center justify-end gap-3 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-soft-sand/40">
                    <span className="text-[11px] font-sans text-iron-grey/75 bg-soft-sand/50 border border-soft-sand px-2 py-0.5 rounded font-medium">
                      Pending
                    </span>
                    <button
                      type="button"
                      disabled={actionLoadingId === reqId}
                      onClick={() => handleCancel(reqId)}
                      className="text-xs font-sans text-iron-grey hover:text-deep-crimson hover:bg-soft-sand/40 px-2.5 py-1.5 rounded transition-colors disabled:opacity-50"
                      title="Cancel invitation"
                    >
                      {actionLoadingId === reqId ? 'Cancelling...' : 'Cancel Request'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )
      )}
    </div>
  );
}
