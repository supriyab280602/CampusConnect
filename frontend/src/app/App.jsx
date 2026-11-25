import React, { useState, useEffect } from 'react';
import { AuthProvider, useAuth } from '../context/AuthContext';
import { ToastProvider } from '../context/ToastContext';
import { LoginView } from '../components/auth/LoginView';
import { RegisterView } from '../components/auth/RegisterView';
import { AppLayout } from '../components/layout/AppLayout';
import { FeedView } from '../components/feed/FeedView';
import { DiscoveryView } from '../components/discovery/DiscoveryView';
import { ConnectionsView } from '../components/connections/ConnectionsView';
import { NetworkView } from '../components/network/NetworkView';
import { ProfileView } from '../components/profile/ProfileView';

function MainApp() {
  const { isAuthenticated, loading } = useAuth();
  const [authMode, setAuthMode] = useState('login'); // 'login' | 'register'
  const [activeTab, setActiveTab] = useState('feed'); // 'feed' | 'discover' | 'connections' | 'network' | 'profile'
  const [selectedUserId, setSelectedUserId] = useState(null);

  // Sync tab with URL search parameter if present
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const tabParam = params.get('tab');
    if (tabParam && ['feed', 'discover', 'connections', 'network', 'profile'].includes(tabParam)) {
      setActiveTab(tabParam);
    }
  }, []);

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setSelectedUserId(null); // Clear peer profile view when switching tabs
    const url = new URL(window.location.href);
    url.searchParams.set('tab', tab);
    window.history.pushState({}, '', url);
  };

  const handleSelectUser = (userId) => {
    setSelectedUserId(userId);
    setActiveTab('profile');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-warm-porcelain flex flex-col items-center justify-center p-4">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-vivid-tangerine flex items-center justify-center text-white font-bold text-2xl shadow-md animate-pulse">
            CC
          </div>
          <div className="text-center">
            <h1 className="text-xl font-serif font-bold text-shadow-grey">CampusConnect</h1>
            <p className="text-xs text-iron-grey tracking-wider uppercase mt-1">Initializing University Engine...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return authMode === 'login' ? (
      <LoginView onSwitchToRegister={() => setAuthMode('register')} />
    ) : (
      <RegisterView onSwitchToLogin={() => setAuthMode('login')} />
    );
  }

  return (
    <AppLayout activeTab={activeTab} onTabChange={handleTabChange}>
      {activeTab === 'feed' && <FeedView onSelectUser={handleSelectUser} />}
      {activeTab === 'discover' && <DiscoveryView onSelectUser={handleSelectUser} />}
      {activeTab === 'connections' && <ConnectionsView onSelectUser={handleSelectUser} />}
      {activeTab === 'network' && <NetworkView onSelectUser={handleSelectUser} />}
      {activeTab === 'profile' && (
        <ProfileView
          selectedUserId={selectedUserId}
          onClearSelectedUser={() => setSelectedUserId(null)}
        />
      )}
    </AppLayout>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <ToastProvider>
        <MainApp />
      </ToastProvider>
    </AuthProvider>
  );
}
