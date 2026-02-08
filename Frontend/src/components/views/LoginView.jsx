import { useState } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { C } from '../../constants/theme';
import Button from '../ui/Button';
import LoadingSpinner from '../shared/LoadingSpinner';

export default function LoginView() {
  const { login, register, error, clearError, isLoading } = useAuth();
  const [mode, setMode] = useState('login'); // 'login' or 'register'
  const [formData, setFormData] = useState({
    emailOrUsername: '',
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
    fullName: '',
  });
  const [formError, setFormError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    setFormError('');
    clearError();
  };

  const validateForm = () => {
    if (mode === 'login') {
      if (!formData.emailOrUsername.trim()) {
        setFormError('Email or username is required');
        return false;
      }
      if (!formData.password) {
        setFormError('Password is required');
        return false;
      }
    } else {
      if (!formData.email.trim()) {
        setFormError('Email is required');
        return false;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        setFormError('Invalid email format');
        return false;
      }
      if (!formData.username.trim()) {
        setFormError('Username is required');
        return false;
      }
      if (formData.username.length < 3) {
        setFormError('Username must be at least 3 characters');
        return false;
      }
      if (!formData.password) {
        setFormError('Password is required');
        return false;
      }
      if (formData.password.length < 8) {
        setFormError('Password must be at least 8 characters');
        return false;
      }
      if (formData.password !== formData.confirmPassword) {
        setFormError('Passwords do not match');
        return false;
      }
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    try {
      if (mode === 'login') {
        await login(formData.emailOrUsername, formData.password);
      } else {
        await register(
          formData.email,
          formData.username,
          formData.password,
          formData.fullName || null
        );
        // After successful registration, switch to login mode
        setMode('login');
        setFormData((prev) => ({
          ...prev,
          emailOrUsername: formData.email,
          password: '',
        }));
        setFormError('');
      }
    } catch {
      // Error is handled by AuthContext
    }
  };

  const switchMode = () => {
    setMode((prev) => (prev === 'login' ? 'register' : 'login'));
    setFormError('');
    clearError();
  };

  const inputStyle = {
    width: '100%',
    padding: '12px 16px',
    fontSize: '14px',
    background: C.surface,
    border: `1px solid ${C.border}`,
    borderRadius: '8px',
    color: C.text,
    outline: 'none',
    transition: 'border-color 0.2s, box-shadow 0.2s',
  };

  const inputFocusStyle = {
    borderColor: C.accent,
    boxShadow: `0 0 0 2px ${C.accentMuted}`,
  };

  const labelStyle = {
    display: 'block',
    marginBottom: '8px',
    fontSize: '13px',
    fontWeight: 500,
    color: C.textMuted,
  };

  const errorMessage = formError || error;

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: '24px',
        background: C.bg,
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: '400px',
          padding: '40px',
          background: C.surface,
          borderRadius: '16px',
          border: `1px solid ${C.border}`,
        }}
      >
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h1
            style={{
              fontSize: '24px',
              fontWeight: 700,
              color: C.text,
              margin: '0 0 8px',
            }}
          >
            {mode === 'login' ? 'Welcome Back' : 'Create Account'}
          </h1>
          <p style={{ fontSize: '14px', color: C.textMuted, margin: 0 }}>
            {mode === 'login'
              ? 'Sign in to your account to continue'
              : 'Create a new account to get started'}
          </p>
        </div>

        {errorMessage && (
          <div
            role="alert"
            style={{
              padding: '12px 16px',
              marginBottom: '24px',
              background: C.dangerMuted,
              border: `1px solid ${C.danger}`,
              borderRadius: '8px',
              color: C.danger,
              fontSize: '13px',
            }}
          >
            {errorMessage}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {mode === 'login' ? (
            <>
              <div style={{ marginBottom: '20px' }}>
                <label htmlFor="emailOrUsername" style={labelStyle}>
                  Email or Username
                </label>
                <input
                  id="emailOrUsername"
                  name="emailOrUsername"
                  type="text"
                  value={formData.emailOrUsername}
                  onChange={handleChange}
                  style={inputStyle}
                  onFocus={(e) => Object.assign(e.target.style, inputFocusStyle)}
                  onBlur={(e) => {
                    e.target.style.borderColor = C.border;
                    e.target.style.boxShadow = 'none';
                  }}
                  autoComplete="username"
                  autoFocus
                />
              </div>

              <div style={{ marginBottom: '24px' }}>
                <label htmlFor="password" style={labelStyle}>
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  value={formData.password}
                  onChange={handleChange}
                  style={inputStyle}
                  onFocus={(e) => Object.assign(e.target.style, inputFocusStyle)}
                  onBlur={(e) => {
                    e.target.style.borderColor = C.border;
                    e.target.style.boxShadow = 'none';
                  }}
                  autoComplete="current-password"
                />
              </div>
            </>
          ) : (
            <>
              <div style={{ marginBottom: '20px' }}>
                <label htmlFor="fullName" style={labelStyle}>
                  Full Name (optional)
                </label>
                <input
                  id="fullName"
                  name="fullName"
                  type="text"
                  value={formData.fullName}
                  onChange={handleChange}
                  style={inputStyle}
                  onFocus={(e) => Object.assign(e.target.style, inputFocusStyle)}
                  onBlur={(e) => {
                    e.target.style.borderColor = C.border;
                    e.target.style.boxShadow = 'none';
                  }}
                  autoComplete="name"
                  autoFocus
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label htmlFor="email" style={labelStyle}>
                  Email
                </label>
                <input
                  id="email"
                  name="email"
                  type="email"
                  value={formData.email}
                  onChange={handleChange}
                  style={inputStyle}
                  onFocus={(e) => Object.assign(e.target.style, inputFocusStyle)}
                  onBlur={(e) => {
                    e.target.style.borderColor = C.border;
                    e.target.style.boxShadow = 'none';
                  }}
                  autoComplete="email"
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label htmlFor="username" style={labelStyle}>
                  Username
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  value={formData.username}
                  onChange={handleChange}
                  style={inputStyle}
                  onFocus={(e) => Object.assign(e.target.style, inputFocusStyle)}
                  onBlur={(e) => {
                    e.target.style.borderColor = C.border;
                    e.target.style.boxShadow = 'none';
                  }}
                  autoComplete="username"
                />
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label htmlFor="registerPassword" style={labelStyle}>
                  Password
                </label>
                <input
                  id="registerPassword"
                  name="password"
                  type="password"
                  value={formData.password}
                  onChange={handleChange}
                  style={inputStyle}
                  onFocus={(e) => Object.assign(e.target.style, inputFocusStyle)}
                  onBlur={(e) => {
                    e.target.style.borderColor = C.border;
                    e.target.style.boxShadow = 'none';
                  }}
                  autoComplete="new-password"
                />
              </div>

              <div style={{ marginBottom: '24px' }}>
                <label htmlFor="confirmPassword" style={labelStyle}>
                  Confirm Password
                </label>
                <input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  value={formData.confirmPassword}
                  onChange={handleChange}
                  style={inputStyle}
                  onFocus={(e) => Object.assign(e.target.style, inputFocusStyle)}
                  onBlur={(e) => {
                    e.target.style.borderColor = C.border;
                    e.target.style.boxShadow = 'none';
                  }}
                  autoComplete="new-password"
                />
              </div>
            </>
          )}

          <Button
            type="submit"
            disabled={isLoading}
            style={{
              width: '100%',
              padding: '14px',
              fontSize: '15px',
              fontWeight: 600,
            }}
          >
            {isLoading ? (
              <LoadingSpinner size="small" inline />
            ) : mode === 'login' ? (
              'Sign In'
            ) : (
              'Create Account'
            )}
          </Button>
        </form>

        <div
          style={{
            marginTop: '24px',
            textAlign: 'center',
            fontSize: '13px',
            color: C.textMuted,
          }}
        >
          {mode === 'login' ? (
            <>
              Don&apos;t have an account?{' '}
              <button
                type="button"
                onClick={switchMode}
                style={{
                  background: 'none',
                  border: 'none',
                  color: C.accent,
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: 500,
                  padding: 0,
                }}
              >
                Create one
              </button>
            </>
          ) : (
            <>
              Already have an account?{' '}
              <button
                type="button"
                onClick={switchMode}
                style={{
                  background: 'none',
                  border: 'none',
                  color: C.accent,
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: 500,
                  padding: 0,
                }}
              >
                Sign in
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
