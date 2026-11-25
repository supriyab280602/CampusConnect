import React from 'react';
import { Navbar } from './Navbar';
import { Sidebar } from './Sidebar';

export function AppLayout({ activeTab, onTabChange, children }) {
  return (
    <div className="min-h-screen bg-warm-porcelain flex flex-col text-shadow-grey overflow-x-hidden">
      <Navbar activeTab={activeTab} onTabChange={onTabChange} />

      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-5 sm:py-6 pb-24 md:pb-8">
        <div className="flex flex-col lg:flex-row gap-6">
          {/* Left Sidebar (Desktop only) */}
          <div className="hidden lg:block w-64 shrink-0">
            <Sidebar activeTab={activeTab} onTabChange={onTabChange} />
          </div>

          {/* Primary View Content */}
          <div className="flex-1 min-w-0">
            {children}
          </div>
        </div>
      </main>

      {/* Editorial Footer (spaced so mobile bottom nav doesn't occlude) */}
      <footer className="border-t border-soft-sand/80 py-4 text-center text-xs text-iron-grey bg-white/40 mb-16 md:mb-0 select-none">
        CampusConnect &middot; Academic DSA Implementation &middot; Chanakya University
      </footer>
    </div>
  );
}
