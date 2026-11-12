import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function App() {
  const [healthStatus, setHealthStatus] = useState('loading');
  const [healthData, setHealthData] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    let isMounted = true;

    api.get('/health')
      .then((res) => {
        if (isMounted) {
          if (res && res.data && res.data.status === 'healthy') {
            setHealthStatus('healthy');
            setHealthData(res.data);
          } else {
            setHealthStatus('unexpected');
            setErrorMessage('Unexpected response structure');
          }
        }
      })
      .catch((err) => {
        if (isMounted) {
          setHealthStatus('error');
          setErrorMessage(err.message || 'Failed to connect to backend');
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <div className="min-h-screen bg-warm-porcelain flex flex-col justify-between p-6 sm:p-12">
      <header className="max-w-4xl mx-auto w-full pt-8">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-vivid-tangerine flex items-center justify-center text-white font-bold text-xl shadow-sm">
            CC
          </div>
          <div>
            <h1 className="text-3xl sm:text-4xl font-serif text-shadow-grey font-semibold tracking-tight">
              CampusConnect
            </h1>
            <p className="text-sm font-sans text-iron-grey tracking-wide uppercase">
              University Networking Platform &middot; DSA Core Engine
            </p>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto w-full py-12 flex-1 flex flex-col justify-center">
        <div className="bg-white border border-soft-sand rounded-xl p-8 shadow-sm">
          <h2 className="text-2xl font-serif text-shadow-grey mb-3">
            Phase 0 Foundation Baseline
          </h2>
          <p className="text-iron-grey font-sans mb-6 text-sm leading-relaxed">
            Welcome to CampusConnect. The frontend and backend foundations are active, verifying cross-origin communication, native fetch integration, and server-managed session readiness.
          </p>

          <div className="pt-4 border-t border-soft-sand">
            <h3 className="text-xs font-semibold text-iron-grey uppercase tracking-wider mb-2">
              Backend Health Status Probe
            </h3>

            {healthStatus === 'loading' && (
              <div id="api-status" data-status="loading" className="inline-flex items-center space-x-2 text-sm text-iron-grey bg-soft-sand/40 px-3 py-1.5 rounded-md">
                <span className="w-2 h-2 rounded-full bg-iron-grey animate-pulse"></span>
                <span>Connecting to backend at /api/v1/health...</span>
              </div>
            )}

            {healthStatus === 'healthy' && (
              <div id="api-status" data-status="healthy" className="inline-flex items-center space-x-2 text-sm text-emerald-800 bg-emerald-50 border border-emerald-200 px-3 py-1.5 rounded-md">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                <span>Connected: {healthData?.service} v{healthData?.version} (Status: {healthData?.status})</span>
              </div>
            )}

            {healthStatus === 'error' && (
              <div id="api-status" data-status="error" className="inline-flex items-center space-x-2 text-sm text-deep-crimson bg-red-50 border border-red-200 px-3 py-1.5 rounded-md">
                <span className="w-2 h-2 rounded-full bg-deep-crimson"></span>
                <span>Connection Error: {errorMessage}</span>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="max-w-4xl mx-auto w-full text-center text-xs text-iron-grey py-6 border-t border-soft-sand/60">
        CampusConnect &middot; Academic Year 2026&ndash;27 &middot; Chanakya University
      </footer>
    </div>
  );
}

