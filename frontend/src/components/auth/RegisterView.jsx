import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useToast } from '../../context/ToastContext';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { Card } from '../common/Card';

export function RegisterView({ onSwitchToLogin }) {
  const { register } = useAuth();
  const { showToast } = useToast();
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    full_name: '',
    programme: 'Computer Science',
    academic_year: 1,
    skills: '',
    bio: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.username.trim() || !formData.email.trim() || !formData.password || !formData.full_name.trim()) {
      setError('Please fill in all required fields.');
      return;
    }

    try {
      setLoading(true);
      setError('');
      const skillsArray = formData.skills
        ? formData.skills.split(',').map((s) => s.trim()).filter(Boolean)
        : [];

      await register({
        username: formData.username.trim(),
        email: formData.email.trim(),
        password: formData.password,
        full_name: formData.full_name.trim(),
        programme: formData.programme.trim() || 'General Studies',
        academic_year: parseInt(formData.academic_year, 10) || 1,
        skills: skillsArray,
        bio: formData.bio.trim() || null,
      });

      showToast('Account created successfully! Welcome to CampusConnect.');
    } catch (err) {
      setError(err.message || 'Registration failed. Username or email may already be registered.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-warm-porcelain flex items-center justify-center p-4">
      <Card className="w-full max-w-lg p-8">
        <div className="flex flex-col items-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-vivid-tangerine flex items-center justify-center text-white font-bold text-2xl shadow-sm mb-3">
            CC
          </div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-shadow-grey text-center">
            Join CampusConnect
          </h1>
          <p className="text-xs text-iron-grey mt-1 text-center">
            Create your university identity & connect with fellow students
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-deep-crimson text-xs rounded-lg font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <Input
              label="Full Name"
              name="full_name"
              value={formData.full_name}
              onChange={handleChange}
              placeholder="e.g. Alex Smith"
              required
            />
            <Input
              label="Username"
              name="username"
              value={formData.username}
              onChange={handleChange}
              placeholder="e.g. alex_smith"
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <Input
              label="University Email"
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="alex@university.edu"
              required
            />
            <Input
              label="Password"
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              placeholder="Minimum 6 characters"
              required
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
            <Input
              label="Academic Programme"
              name="programme"
              value={formData.programme}
              onChange={handleChange}
              placeholder="e.g. Computer Science"
              required
            />
            <Input
              label="Academic Year"
              type="number"
              name="academic_year"
              min="1"
              max="6"
              value={formData.academic_year}
              onChange={handleChange}
              required
            />
          </div>

          <Input
            label="Technical Skills"
            name="skills"
            value={formData.skills}
            onChange={handleChange}
            placeholder="e.g. Python, React, Algorithms (comma-separated)"
          />

          <div className="flex flex-col space-y-1.5">
            <label htmlFor="register-bio" className="text-xs font-semibold text-iron-grey uppercase tracking-wider">
              Student Bio
            </label>
            <textarea
              id="register-bio"
              name="bio"
              rows={2}
              value={formData.bio}
              onChange={handleChange}
              placeholder="Brief description of your academic interests..."
              className="w-full px-3.5 py-2 text-sm bg-white border border-soft-sand rounded-lg text-shadow-grey placeholder:text-iron-grey/50 focus:outline-none focus:ring-2 focus:ring-vivid-tangerine hover:border-ash-grey transition-colors"
            />
          </div>

          <Button type="submit" variant="primary" size="lg" className="w-full mt-3" loading={loading}>
            Create Account
          </Button>
        </form>

        <div className="mt-6 pt-4 border-t border-soft-sand text-center text-xs text-iron-grey">
          Already registered?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="font-semibold text-vivid-tangerine hover:underline focus:outline-none"
          >
            Sign in here
          </button>
        </div>
      </Card>
    </div>
  );
}
