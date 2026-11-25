import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Card } from '../common/Card';

export function LoginView({ onSwitchToRegister }) {
  const { login } = useAuth();
  const { showToast } = useToast();
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!identifier.trim() || !password) {
      setError('Please provide your username/email and password.');
      return;
    }

    try {
      setLoading(true);
      setError('');
      await login(identifier.trim(), password);
      showToast('Logged in successfully!');
    } catch (err) {
      setError(err.message || 'Invalid credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-warm-porcelain flex items-center justify-center p-4">
      <Card className="w-full max-w-md p-8">
        <div className="flex flex-col items-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-vivid-tangerine flex items-center justify-center text-white font-bold text-2xl shadow-sm mb-3">
            CC
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-shadow-grey text-center">
            Welcome Back
          </h1>
          <p className="text-xs text-iron-grey mt-1 text-center">
            Sign in to your CampusConnect student account
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-deep-crimson text-xs rounded-lg font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <Input
            label="Username or Email"
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            placeholder="e.g. alex_cs or alex@university.edu"
            required
            autoFocus
          />

          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            required
          />

          <Button type="submit" variant="primary" size="lg" className="w-full mt-2" loading={loading}>
            Sign In
          </Button>
        </form>

        <div className="mt-6 pt-4 border-t border-soft-sand text-center text-xs text-iron-grey">
          Don't have an account yet?{' '}
          <button
            type="button"
            onClick={onSwitchToRegister}
            className="font-semibold text-vivid-tangerine hover:underline focus:outline-none"
          >
            Create an Account
          </button>
        </div>
      </Card>
    </div>
  );
}
