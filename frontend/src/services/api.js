const RAW_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const API_BASE_URL = RAW_API_BASE_URL.replace(/\/+$/, '');
const TOKEN_STORAGE_KEY = 'campusconnect_token';

// Auth endpoints that emit X-Session-Token we should capture
const AUTH_TOKEN_ENDPOINTS = ['/auth/login', '/auth/register'];

async function request(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const headers = {
    'Accept': 'application/json',
    // X-Requested-With tells the backend this is an XHR/fetch request (CSRF mitigation)
    'X-Requested-With': 'XMLHttpRequest',
    ...(options.headers || {}),
  };

  // Attach Content-Type only when a body is present
  if (options.body && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  // Attach Authorization Bearer token if present (for cross-origin deployments where
  // third-party cookies are blocked by the browser)
  if (typeof window !== 'undefined' && !headers['Authorization']) {
    try {
      const token = sessionStorage.getItem(TOKEN_STORAGE_KEY);
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    } catch {}
  }

  const config = {
    ...options,
    headers,
    credentials: 'include', // Always send cookies when same-origin or allowed cross-origin
  };

  try {
    const response = await fetch(url, config);

    // Capture X-Session-Token ONLY from auth endpoints (login / register)
    // to avoid stale token overwrites from other responses
    const isAuthEndpoint = AUTH_TOKEN_ENDPOINTS.some(ep => endpoint.includes(ep));
    if (isAuthEndpoint) {
      const sessionToken = response.headers.get('X-Session-Token');
      if (typeof window !== 'undefined') {
        try {
          if (sessionToken && sessionToken.trim() && sessionToken !== 'undefined') {
            sessionStorage.setItem(TOKEN_STORAGE_KEY, sessionToken.trim());
          } else if (sessionToken === '' || sessionToken === null) {
            // Explicit empty means logout cleared the token
            sessionStorage.removeItem(TOKEN_STORAGE_KEY);
          }
        } catch {}
      }
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      if (response.status === 401 && typeof window !== 'undefined') {
        try {
          sessionStorage.removeItem(TOKEN_STORAGE_KEY);
          sessionStorage.removeItem('campusconnect_user');
        } catch {}
        // Notify AuthContext to reset state, unless this is the login endpoint itself
        if (!endpoint.includes('/auth/login')) {
          window.dispatchEvent(new CustomEvent('campusconnect:unauthorized'));
        }
      }
      const error = new Error((data && data.message) || `HTTP error ${response.status}`);
      error.status = response.status;
      error.data = data;
      throw error;
    }

    return data;
  } catch (err) {
    if (!err.status) {
      err.isNetworkError = true;
    }
    throw err;
  }
}

export const api = {
  get: (endpoint, options) => request(endpoint, { ...options, method: 'GET' }),
  post: (endpoint, body, options) => request(endpoint, { ...options, method: 'POST', body: JSON.stringify(body) }),
  put: (endpoint, body, options) => request(endpoint, { ...options, method: 'PUT', body: JSON.stringify(body) }),
  delete: (endpoint, options) => request(endpoint, { ...options, method: 'DELETE' }),
};
