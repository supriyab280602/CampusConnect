import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { api } from '../../services/api';
import { Button } from '../common/Button';
import { Avatar } from '../common/Avatar';

export function ProfileView({ selectedUserId, onClearSelectedUser }) {
  const { currentUser, refreshUser } = useAuth();
  const { showToast } = useToast();

  const isOwnProfile = !selectedUserId || selectedUserId === currentUser?.user_id;
  const activeUserId = isOwnProfile ? currentUser?.user_id : selectedUserId;

  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [degree, setDegree] = useState(0);

  // In-page editing state (strictly for own profile)
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({
    full_name: '',
    programme: '',
    academic_year: 1,
    skills: '',
    bio: '',
  });
  const [saving, setSaving] = useState(false);

  // Peer relationship tracking
  const [isConnected, setIsConnected] = useState(false);
  const [isPending, setIsPending] = useState(false);
  const [sendingRequest, setSendingRequest] = useState(false);

  const fetchProfileData = useCallback(async (uid) => {
    if (!uid) return;
    try {
      setLoading(true);
      const calls = [
        api.get(`/users/${uid}`),
        api.get(`/network/${uid}/degree`),
      ];

      // If viewing peer, also check relationship state
      if (uid !== currentUser?.user_id) {
        calls.push(api.get('/connections'));
        calls.push(api.get('/connections/requests/sent'));
      }

      const results = await Promise.allSettled(calls);
      const [userRes, degRes, connRes, sentRes] = results;

      if (userRes?.status === 'fulfilled' && userRes.value?.success) {
        setProfile(userRes.value.data.user || userRes.value.data);
      }
      if (degRes?.status === 'fulfilled' && degRes.value?.success && typeof degRes.value.data?.degree === 'number') {
        setDegree(degRes.value.data.degree);
      }
      if (connRes?.status === 'fulfilled' && connRes.value?.success) {
        const conns = connRes.value.data?.connections || [];
        const isConn = conns.some((c) => (c.user_id || c.id || c.user?.user_id) === uid);
        setIsConnected(isConn);
      }
      if (sentRes?.status === 'fulfilled' && sentRes.value?.success) {
        const sent = sentRes.value.data?.requests || [];
        const isPend = sent.some((r) => (!r.status || r.status === 'pending') && (r.receiver_id || r.receiver?.user_id) === uid);
        setIsPending(isPend);
      }
    } catch (err) {
      showToast(err.message || 'Could not load student profile', 'error');
    } finally {
      setLoading(false);
    }
  }, [currentUser?.user_id, showToast]);

  useEffect(() => {
    setIsEditing(false);
    if (activeUserId) {
      fetchProfileData(activeUserId);
    }
  }, [activeUserId, fetchProfileData]);

  const handleStartEdit = () => {
    if (!isOwnProfile) return;
    setEditForm({
      full_name: profile?.full_name || currentUser?.full_name || '',
      programme: profile?.programme || currentUser?.programme || 'Computer Science',
      academic_year: profile?.academic_year || currentUser?.academic_year || 1,
      skills: Array.isArray(profile?.skills) ? profile.skills.join(', ') : '',
      bio: profile?.bio || '',
    });
    setIsEditing(true);
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
  };

  const handleSaveProfile = async (e) => {
    e.preventDefault();
    if (!isOwnProfile) return;

    if (!editForm.full_name.trim()) {
      showToast('Full name cannot be blank', 'error');
      return;
    }

    try {
      setSaving(true);
      const skillsArray = editForm.skills
        ? editForm.skills.split(',').map((s) => s.trim()).filter(Boolean)
        : [];

      const res = await api.put('/users/me', {
        full_name: editForm.full_name.trim(),
        programme: editForm.programme.trim() || 'General Studies',
        academic_year: parseInt(editForm.academic_year, 10) || 1,
        skills: skillsArray,
        bio: editForm.bio.trim() || null,
      });

      if (res?.success) {
        const updated = res.data.user || res.data;
        setProfile(updated);
        showToast('Profile updated and synchronized');
        setIsEditing(false);
        await refreshUser();
      }
    } catch (err) {
      showToast(err.message || 'Failed to update profile', 'error');
    } finally {
      setSaving(false);
    }
  };

  const handleSendRequest = async () => {
    const targetUserId = profile?.user_id || selectedUserId;
    if (!targetUserId) return;
    try {
      setSendingRequest(true);
      const res = await api.post('/connections/requests', { receiver_id: targetUserId });
      if (res?.success) {
        showToast('Connection request sent');
        setIsPending(true);
      }
    } catch (err) {
      const msg = err.message || '';
      if (msg.toLowerCase().includes('pending') || msg.toLowerCase().includes('already exists')) {
        setIsPending(true);
        showToast('Connection request already pending', 'info');
      } else if (msg.toLowerCase().includes('already connected')) {
        setIsConnected(true);
        showToast('Already connected with this student', 'info');
      } else {
        showToast(msg || 'Could not send request', 'error');
      }
    } finally {
      setSendingRequest(false);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return '';
    try {
      const date = new Date(isoString);
      return date.toLocaleDateString(undefined, {
        month: 'long',
        year: 'numeric',
      });
    } catch {
      return isoString;
    }
  };

  if (loading) {
    return (
      <div className="space-y-4 max-w-2xl" aria-label="Loading profile">
        <div className="bg-white rounded-xl border border-soft-sand/70 p-6 space-y-4 animate-pulse">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-soft-sand/70 shrink-0"></div>
            <div className="space-y-2 flex-1">
              <div className="h-5 bg-soft-sand/70 rounded w-44"></div>
              <div className="h-3 bg-soft-sand/40 rounded w-28"></div>
            </div>
          </div>
          <div className="space-y-2 pt-2">
            <div className="h-3.5 bg-soft-sand/50 rounded w-full"></div>
            <div className="h-3.5 bg-soft-sand/50 rounded w-4/5"></div>
          </div>
        </div>
      </div>
    );
  }

  const skills = Array.isArray(profile?.skills) ? profile.skills : [];

  return (
    <div className="space-y-6 max-w-2xl">
      {/* 1. Peer Navigation Breadcrumb */}
      {!isOwnProfile && (
        <div className="flex items-center justify-between pb-2 border-b border-soft-sand/70 text-xs font-sans">
          <button
            type="button"
            onClick={onClearSelectedUser}
            className="inline-flex items-center gap-1.5 text-iron-grey hover:text-shadow-grey font-medium transition-colors"
          >
            <span>&larr;</span>
            <span>Return to My Profile</span>
          </button>
          <span className="text-[11px] text-iron-grey/70 bg-soft-sand/40 px-2 py-0.5 rounded border border-soft-sand/60">
            Student Profile
          </span>
        </div>
      )}

      {/* 2. Main Identity Surface */}
      <section aria-label="Student Identity" className="bg-white rounded-xl border border-soft-sand/80 shadow-subtle p-5 sm:p-7 space-y-6">
        {/* Header Block: Avatar + Name + Actions */}
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
          <div className="flex items-start gap-4 min-w-0">
            <Avatar
              name={profile?.full_name || profile?.username}
              size="xl"
              className="shrink-0 ring-2 ring-soft-sand/70 shadow-subtle"
            />
            <div className="min-w-0">
              <h1 className="text-xl sm:text-2xl font-serif font-bold text-shadow-grey tracking-tight truncate">
                {profile?.full_name}
              </h1>
              <p className="text-xs text-iron-grey font-sans truncate mt-0.5">
                @{profile?.username}
              </p>

              {/* Department & Academic Year */}
              <p className="text-xs text-shadow-grey/90 font-sans mt-1.5 font-medium truncate">
                {profile?.programme || profile?.department || 'General Studies'}
                {profile?.academic_year ? (
                  <span className="text-iron-grey font-normal"> &middot; Class Year {profile.academic_year}</span>
                ) : null}
              </p>

              {/* Verified Metrics / Status Chips */}
              <div className="flex flex-wrap items-center gap-2 mt-2.5 text-xs font-sans">
                <span className="inline-flex items-center gap-1 bg-warm-porcelain border border-soft-sand px-2.5 py-1 rounded-md text-[11px] text-shadow-grey font-medium">
                  <span className="w-1.5 h-1.5 rounded-full bg-deep-crimson"></span>
                  <span>{degree} Accepted Connection{degree !== 1 ? 's' : ''}</span>
                </span>

                {profile?.created_at && (
                  <span className="text-[11px] text-iron-grey/70 hidden sm:inline">
                    Member since {formatDate(profile.created_at)}
                  </span>
                )}
              </div>
            </div>
          </div>

          {/* Action Button: Edit Profile (Own) or Connect (Peer) */}
          <div className="shrink-0 pt-1 sm:pt-0">
            {isOwnProfile ? (
              !isEditing && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleStartEdit}
                  className="font-medium text-xs px-3.5 shadow-subtle"
                >
                  Edit Profile
                </Button>
              )
            ) : (
              <div>
                {isConnected ? (
                  <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-800 bg-emerald-50 border border-emerald-200/80 px-3 py-1.5 rounded-md">
                    <svg className="w-3.5 h-3.5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" />
                    </svg>
                    Connected
                  </span>
                ) : isPending ? (
                  <span className="inline-flex items-center gap-1 text-[11px] font-medium text-iron-grey bg-soft-sand/50 border border-soft-sand px-3 py-1.5 rounded-md">
                    Request Pending
                  </span>
                ) : (
                  <Button
                    variant="primary"
                    size="sm"
                    disabled={sendingRequest}
                    loading={sendingRequest}
                    onClick={handleSendRequest}
                    className="font-medium text-xs px-4 shadow-subtle"
                  >
                    Connect
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* 3. In-Page Editing Mode */}
        {isEditing ? (
          <form onSubmit={handleSaveProfile} className="pt-4 border-t border-soft-sand/70 space-y-4">
            <div className="flex items-center justify-between pb-1">
              <h2 className="text-sm font-serif font-bold text-shadow-grey uppercase tracking-wider">
                Edit Student Profile
              </h2>
              <span className="text-[11px] text-iron-grey font-sans">
                Changes will sync to the university search Trie
              </span>
            </div>

            <div className="space-y-3.5">
              <div>
                <label htmlFor="edit-fullname" className="block text-xs font-semibold text-iron-grey font-sans mb-1">
                  Full Name <span className="text-deep-crimson">*</span>
                </label>
                <input
                  id="edit-fullname"
                  name="full_name"
                  type="text"
                  required
                  value={editForm.full_name}
                  onChange={(e) => setEditForm((p) => ({ ...p, full_name: e.target.value }))}
                  className="w-full bg-warm-porcelain/40 focus:bg-white text-sm text-shadow-grey rounded-lg px-3 py-2 border border-soft-sand/80 focus:border-iron-grey/40 focus:outline-none focus:ring-1 focus:ring-iron-grey/25 font-sans"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label htmlFor="edit-programme" className="block text-xs font-semibold text-iron-grey font-sans mb-1">
                    Programme / Department <span className="text-deep-crimson">*</span>
                  </label>
                  <input
                    id="edit-programme"
                    name="programme"
                    type="text"
                    required
                    value={editForm.programme}
                    onChange={(e) => setEditForm((p) => ({ ...p, programme: e.target.value }))}
                    className="w-full bg-warm-porcelain/40 focus:bg-white text-sm text-shadow-grey rounded-lg px-3 py-2 border border-soft-sand/80 focus:border-iron-grey/40 focus:outline-none focus:ring-1 focus:ring-iron-grey/25 font-sans"
                  />
                </div>

                <div>
                  <label htmlFor="edit-year" className="block text-xs font-semibold text-iron-grey font-sans mb-1">
                    Academic Year <span className="text-deep-crimson">*</span>
                  </label>
                  <input
                    id="edit-year"
                    name="academic_year"
                    type="number"
                    min="1"
                    max="6"
                    required
                    value={editForm.academic_year}
                    onChange={(e) => setEditForm((p) => ({ ...p, academic_year: e.target.value }))}
                    className="w-full bg-warm-porcelain/40 focus:bg-white text-sm text-shadow-grey rounded-lg px-3 py-2 border border-soft-sand/80 focus:border-iron-grey/40 focus:outline-none focus:ring-1 focus:ring-iron-grey/25 font-sans"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="edit-skills" className="block text-xs font-semibold text-iron-grey font-sans mb-1">
                  Skills &amp; Technical Competencies
                </label>
                <input
                  id="edit-skills"
                  name="skills"
                  type="text"
                  placeholder="e.g. Algorithms, React, Flask, Distributed Systems"
                  value={editForm.skills}
                  onChange={(e) => setEditForm((p) => ({ ...p, skills: e.target.value }))}
                  className="w-full bg-warm-porcelain/40 focus:bg-white text-sm text-shadow-grey placeholder:text-iron-grey/50 rounded-lg px-3 py-2 border border-soft-sand/80 focus:border-iron-grey/40 focus:outline-none focus:ring-1 focus:ring-iron-grey/25 font-sans"
                />
                <span className="text-[11px] text-iron-grey/60 font-sans mt-0.5 block">
                  Separate competencies with commas
                </span>
              </div>

              <div>
                <label htmlFor="edit-bio" className="block text-xs font-semibold text-iron-grey font-sans mb-1">
                  Biography &amp; Academic Focus
                </label>
                <textarea
                  id="edit-bio"
                  name="bio"
                  rows={3}
                  placeholder="Introduce your current research projects, thesis focus, or campus interests..."
                  value={editForm.bio}
                  onChange={(e) => setEditForm((p) => ({ ...p, bio: e.target.value }))}
                  className="w-full bg-warm-porcelain/40 focus:bg-white text-sm text-shadow-grey placeholder:text-iron-grey/50 rounded-lg p-3 border border-soft-sand/80 focus:border-iron-grey/40 focus:outline-none focus:ring-1 focus:ring-iron-grey/25 resize-none font-sans"
                />
              </div>
            </div>

            {/* Action Buttons */}
            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-soft-sand/70">
              <Button
                type="button"
                variant="ghost"
                size="sm"
                onClick={handleCancelEdit}
                disabled={saving}
                className="text-xs font-sans px-3"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                loading={saving}
                disabled={saving}
                className="text-xs font-sans px-4 shadow-subtle font-medium"
              >
                Save Changes
              </Button>
            </div>
          </form>
        ) : (
          /* View Mode: Biography & Skills */
          <>
            {/* Biography Section */}
            <div className="pt-4 border-t border-soft-sand/70 space-y-1.5">
              <h2 className="text-xs font-semibold text-iron-grey font-sans uppercase tracking-wider">
                Biography
              </h2>
              {profile?.bio ? (
                <p className="text-[15px] font-serif text-shadow-grey leading-relaxed whitespace-pre-wrap break-words">
                  {profile.bio}
                </p>
              ) : (
                <p className="text-xs text-iron-grey/70 font-sans italic">
                  {isOwnProfile
                    ? 'No biography provided yet. Click "Edit Profile" above to share your academic interests and projects with colleagues.'
                    : 'This student has not added a biography yet.'}
                </p>
              )}
            </div>

            {/* Skills & Technical Competencies */}
            <div className="pt-4 border-t border-soft-sand/70 space-y-2">
              <h2 className="text-xs font-semibold text-iron-grey font-sans uppercase tracking-wider">
                Skills &amp; Competencies
              </h2>
              {skills.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {skills.map((skill, idx) => (
                    <span
                      key={idx}
                      className="bg-warm-porcelain/80 border border-soft-sand px-2.5 py-1 rounded-md text-xs font-sans text-shadow-grey font-medium shadow-subtle"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-iron-grey/70 font-sans italic">
                  {isOwnProfile
                    ? 'No skills listed yet. Add technical skills or research areas via "Edit Profile".'
                    : 'No competencies listed.'}
                </p>
              )}
            </div>
          </>
        )}
      </section>
    </div>
  );
}
