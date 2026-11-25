import React, { useEffect, useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { Avatar } from '../common/Avatar';
import { Card } from '../common/Card';
import { Badge } from '../common/Badge';

export function Sidebar({ activeTab, onTabChange }) {
  const { currentUser } = useAuth();
  const [degree, setDegree] = useState(0);

  useEffect(() => {
    if (currentUser?.user_id) {
      api.get(`/network/${currentUser.user_id}/degree`)
        .then((res) => {
          if (res?.success && typeof res?.data?.degree === 'number') {
            setDegree(res.data.degree);
          }
        })
        .catch(() => {});
    }
  }, [currentUser?.user_id]);

  const isProfileTab = activeTab === 'profile';

  return (
    <aside className="w-full lg:w-64 space-y-4">
      {/* Student Identity Rail */}
      {!isProfileTab ? (
        <Card className="text-center">
          <div className="flex flex-col items-center">
            <div
              className="cursor-pointer group"
              onClick={() => onTabChange('profile')}
              title="View your profile"
            >
              <Avatar
                name={currentUser?.full_name || currentUser?.username}
                size="lg"
                className="mb-2.5 transition-transform group-hover:scale-105"
              />
            </div>
            <h2
              className="font-serif font-semibold text-base text-shadow-grey leading-snug cursor-pointer hover:text-deep-crimson transition-colors"
              onClick={() => onTabChange('profile')}
            >
              {currentUser?.full_name}
            </h2>
            <p className="text-xs text-iron-grey mb-2.5">@{currentUser?.username}</p>

            <div className="flex flex-wrap items-center justify-center gap-1.5 mb-3.5">
              <Badge variant="primary" size="xs">
                {currentUser?.programme || 'General Studies'}
              </Badge>
              <Badge variant="neutral" size="xs">
                Year {currentUser?.academic_year || 1}
              </Badge>
            </div>

            <div className="w-full pt-3 border-t border-soft-sand/80 grid grid-cols-2 text-center text-xs">
              <div
                className="cursor-pointer p-1.5 rounded hover:bg-soft-sand/40 transition-colors"
                onClick={() => onTabChange('connections')}
                title="View your network connections"
              >
                <span className="block font-serif font-bold text-base text-shadow-grey leading-tight">{degree}</span>
                <span className="text-[10px] text-iron-grey uppercase tracking-wider font-semibold">Connections</span>
              </div>
              <div
                className="cursor-pointer p-1.5 rounded hover:bg-soft-sand/40 transition-colors group"
                onClick={() => onTabChange('network')}
                title="Explore shortest paths with BFS"
              >
                <span className="flex items-center justify-center font-serif font-bold text-base text-shadow-grey group-hover:text-deep-crimson transition-colors leading-tight">
                  <svg className="w-3.5 h-3.5 mr-1 text-iron-grey group-hover:text-deep-crimson transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <circle cx="6" cy="6" r="2.5" strokeWidth={2} />
                    <circle cx="18" cy="6" r="2.5" strokeWidth={2} />
                    <circle cx="12" cy="18" r="2.5" strokeWidth={2} />
                    <path strokeWidth={2} d="M8.5 7.5h7M7.5 8.5l3 7M16.5 8.5l-3 7" />
                  </svg>
                  BFS
                </span>
                <span className="text-[10px] text-iron-grey uppercase tracking-wider font-semibold group-hover:text-shadow-grey">Pathfinder</span>
              </div>
            </div>
          </div>
        </Card>
      ) : (
        /* Academic Navigation Rail on Profile Page (prevents double profile repetition) */
        <Card variant="subtle" className="text-xs space-y-3">
          <h3 className="font-serif font-semibold text-shadow-grey text-sm">
            Quick Navigation
          </h3>
          <p className="text-iron-grey text-[11px] leading-relaxed">
            Jump to other campus intelligence modules:
          </p>
          <div className="space-y-1.5 pt-1">
            <button
              onClick={() => onTabChange('feed')}
              className="w-full text-left px-2.5 py-1.5 rounded text-xs text-iron-grey hover:text-shadow-grey hover:bg-soft-sand/50 transition-colors flex items-center justify-between"
            >
              <span>Academic Feed</span>
              <span>&rarr;</span>
            </button>
            <button
              onClick={() => onTabChange('discover')}
              className="w-full text-left px-2.5 py-1.5 rounded text-xs text-iron-grey hover:text-shadow-grey hover:bg-soft-sand/50 transition-colors flex items-center justify-between"
            >
              <span>Student Directory</span>
              <span>&rarr;</span>
            </button>
            <button
              onClick={() => onTabChange('connections')}
              className="w-full text-left px-2.5 py-1.5 rounded text-xs text-iron-grey hover:text-shadow-grey hover:bg-soft-sand/50 transition-colors flex items-center justify-between"
            >
              <span>Connections ({degree})</span>
              <span>&rarr;</span>
            </button>
            <button
              onClick={() => onTabChange('network')}
              className="w-full text-left px-2.5 py-1.5 rounded text-xs text-iron-grey hover:text-shadow-grey hover:bg-soft-sand/50 transition-colors flex items-center justify-between"
            >
              <span>Network Graph & BFS</span>
              <span>&rarr;</span>
            </button>
          </div>
        </Card>
      )}

      {/* Academic Engine Provenance Card */}
      <Card variant="subtle" className="text-xs space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="font-serif font-semibold text-shadow-grey text-xs uppercase tracking-wider">
            Engine Core
          </h3>
          <span className="inline-flex items-center text-[10px] text-emerald-800 font-semibold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200/70">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 mr-1.5 animate-pulse" /> Active
          </span>
        </div>
        <p className="text-iron-grey text-[11px] leading-relaxed">
          Custom adjacency-list Graph traversal, Prefix Trie search, and Min-Heap priority queues.
        </p>
      </Card>
    </aside>
  );
}
