import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { Avatar } from '../common/Avatar';
import { Button } from '../common/Button';

export function Navbar({ activeTab, onTabChange }) {
  const { currentUser, logout } = useAuth();

  const navItems = [
    {
      id: 'feed',
      label: 'Feed',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z" />
        </svg>
      ),
    },
    {
      id: 'discover',
      label: 'Discover',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      ),
    },
    {
      id: 'connections',
      label: 'Connections',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
    },
    {
      id: 'network',
      label: 'Network',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <circle cx="6" cy="6" r="2.5" strokeWidth={1.75} />
          <circle cx="18" cy="6" r="2.5" strokeWidth={1.75} />
          <circle cx="12" cy="18" r="2.5" strokeWidth={1.75} />
          <path strokeWidth={1.75} d="M8.5 7.5h7M7.5 8.5l3 7M16.5 8.5l-3 7" />
        </svg>
      ),
    },
    {
      id: 'profile',
      label: 'Profile',
      icon: (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.75} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      ),
    },
  ];

  return (
    <>
      {/* Top Header Bar */}
      <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-xs border-b border-soft-sand">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14 sm:h-16">
            {/* Campus Branding (Left) */}
            <div
              className="flex items-center space-x-2.5 cursor-pointer shrink-0 select-none"
              onClick={() => onTabChange('feed')}
            >
              <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-md bg-deep-crimson flex items-center justify-center text-warm-porcelain font-serif font-bold text-base shadow-subtle">
                CC
              </div>
              <div>
                <span className="text-lg sm:text-xl font-serif font-semibold tracking-tight text-shadow-grey block leading-none">
                  CampusConnect
                </span>
                <span className="text-[9px] sm:text-[10px] tracking-widest uppercase font-semibold text-iron-grey block mt-0.5">
                  Chanakya University
                </span>
              </div>
            </div>

            {/* Desktop Navigation Tabs (Center) */}
            <nav className="hidden md:flex items-center space-x-1 lg:space-x-2 shrink-0">
              {navItems.map((item) => {
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => onTabChange(item.id)}
                    className={`relative px-3 py-1.5 text-xs font-semibold uppercase tracking-wider transition-colors rounded-md ${
                      isActive
                        ? 'text-deep-crimson font-bold bg-soft-sand/50'
                        : 'text-iron-grey hover:text-shadow-grey hover:bg-soft-sand/30'
                    }`}
                  >
                    {item.label}
                    {isActive && (
                      <span className="absolute bottom-0 left-3 right-3 h-0.5 bg-deep-crimson rounded-full" />
                    )}
                  </button>
                );
              })}
            </nav>

            {/* Simplified User Access & Logout (Right) */}
            <div className="flex items-center space-x-2 sm:space-x-3 shrink-0">
              <button
                type="button"
                onClick={() => onTabChange('profile')}
                className={`flex items-center space-x-2 p-1 rounded-md transition-colors ${
                  activeTab === 'profile' ? 'bg-soft-sand/60 ring-1 ring-deep-crimson/30' : 'hover:bg-soft-sand/40'
                }`}
                title="View Profile"
              >
                <Avatar name={currentUser?.full_name || currentUser?.username} size="sm" />
                <span className="hidden lg:inline text-xs font-medium text-shadow-grey max-w-[120px] truncate">
                  {currentUser?.full_name || currentUser?.username}
                </span>
              </button>

              <Button
                variant="ghost"
                size="sm"
                onClick={logout}
                className="text-xs text-iron-grey hover:text-deep-crimson"
              >
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Modern Fixed Mobile Bottom Navigation Bar (< 768px) */}
      <nav
        aria-label="Mobile Navigation"
        className="md:hidden fixed bottom-0 left-0 right-0 z-50 bg-white/95 backdrop-blur-md border-t border-soft-sand shadow-elevated"
      >
        <div className="flex items-center justify-around h-15 px-2">
          {navItems.map((item) => {
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onTabChange(item.id)}
                className={`flex flex-col items-center justify-center flex-1 py-1.5 transition-colors select-none ${
                  isActive ? 'text-deep-crimson' : 'text-iron-grey hover:text-shadow-grey'
                }`}
              >
                <div className={`p-1 rounded-md transition-colors ${isActive ? 'bg-red-50/70' : ''}`}>
                  {item.icon}
                </div>
                <span className={`text-[10px] mt-0.5 tracking-tight ${isActive ? 'font-bold' : 'font-medium'}`}>
                  {item.label}
                </span>
              </button>
            );
          })}
        </div>
      </nav>
    </>
  );
}
