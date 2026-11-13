import React from 'react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Header from '../components/layout/Header';
import AuthModal from '../components/auth/AuthModal';
import { AuthProvider } from '../context/AuthContext';
import { ThemeProvider } from '../context/ThemeContext';
import client, { getApiBaseUrl } from '../api/client';

describe('Header Component', () => {
  it('renders title and sign-in button for guests', () => {
    render(
      <MemoryRouter>
        <ThemeProvider>
          <AuthProvider>
            <Header title="Placement Assistant Dashboard" />
          </AuthProvider>
        </ThemeProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/Placement Assistant Dashboard/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
  });
});

describe('AuthModal Component', () => {
  it('renders Sign In tab by default with email and password inputs', () => {
    const onClose = vi.fn();
    render(
      <AuthProvider>
        <AuthModal isOpen={true} onClose={onClose} />
      </AuthProvider>
    );

    expect(screen.getByText(/Sign in to your Assistant/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/student@college.edu/i)).toBeInTheDocument();
  });

  it('switches between Sign In and Create Account tabs', () => {
    const onClose = vi.fn();
    render(
      <AuthProvider>
        <AuthModal isOpen={true} onClose={onClose} />
      </AuthProvider>
    );

    const createTab = screen.getByRole('button', { name: /^Create Account$/i });
    fireEvent.click(createTab);

    expect(screen.getByText(/Create Student Account/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/e.g. Arjun Sharma/i)).toBeInTheDocument();
  });
});

describe('Axios API Client', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('resolves default API base URL correctly', () => {
    const url = getApiBaseUrl();
    expect(url).toContain('8000');
  });

  it('attaches Bearer token from localStorage when available', () => {
    const fakeToken = 'sample_jwt_token_12345';
    localStorage.setItem('auth_token', fakeToken);

    const config = { headers: {} };
    // Find interceptor
    const handler = client.interceptors.request.handlers[0];
    expect(handler).toBeDefined();
    if (handler && handler.fulfilled) {
      const updatedConfig = handler.fulfilled(config);
      expect(updatedConfig.headers.Authorization).toBe(`Bearer ${fakeToken}`);
      expect(updatedConfig.baseURL).toContain('8000');
    }
  });
});
