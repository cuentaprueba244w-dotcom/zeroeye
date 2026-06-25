// @ts-nocheck - TODO: Fix types for v2. See V2-619.
/**
 * Authentication service for Tent of Trials.
 * Handles login, logout, token management, MFA, and session tracking.
 *
 * The auth flow supports multiple providers:
 * - Email/password with optional MFA (TOTP, SMS, backup codes)
 * - OAuth2 (Google, GitHub, Microsoft)
 * - SSO (SAML, OpenID Connect)
 * - API key authentication for machine-to-machine
 *
 * Cross-tab token refresh coordination uses BroadcastChannel with
 * localStorage fallback to ensure only one tab performs the network
 * refresh while others adopt the resulting tokens.
 */

import { get, post, del } from './api';

// ---------------------------------------------------------------------------
// TYPES
// ---------------------------------------------------------------------------

export interface User {
  id: string;
  email: string;
  name: string;
  avatarUrl?: string;
  role: UserRole;
  permissions: string[];
  mfaEnabled: boolean;
  emailVerified: boolean;
  createdAt: string;
  updatedAt: string;
  lastLoginAt?: string;
  preferences: UserPreferences;
}

export interface UserPreferences {
  theme: 'light' | 'dark' | 'system';
  language: string;
  timezone: string;
  notifications: NotificationPreferences;
  dashboardLayout?: string;
  marketPreferences?: MarketPreferences;
}

export interface NotificationPreferences {
  email: boolean;
  push: boolean;
  sms: boolean;
  inApp: boolean;
  tradeConfirmations: boolean;
  priceAlerts: boolean;
  accountUpdates: boolean;
  marketing: boolean;
  quietHoursStart?: string;
  quietHoursEnd?: string;
}

export interface MarketPreferences {
  defaultView: 'chart' | 'orderbook' | 'trades';
  defaultInterval: string;
  favoriteInstruments: string[];
  chartPreferences: ChartPreferences;
}

export interface ChartPreferences {
  theme: 'light' | 'dark';
  indicators: string[];
  timeframe: string;
  chartType: 'candlestick' | 'line' | 'area' | 'bar';
  showVolume: boolean;
  showGrid: boolean;
  studies: string[];
}

export type UserRole = 'admin' | 'trader' | 'analyst' | 'viewer' | 'api_only';

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
  tokenType: string;
  scope?: string;
}

export interface LoginRequest {
  email: string;
  password: string;
  mfaCode?: string;
  rememberMe?: boolean;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  acceptTerms: boolean;
  acceptPrivacy: boolean;
  referralCode?: string;
}

// ---------------------------------------------------------------------------
// CONSTANTS
// ---------------------------------------------------------------------------

const TOKEN_KEY = 'tot_auth_tokens';
const REFRESH_THRESHOLD = 60; // seconds before expiry to attempt refresh
const BROADCAST_CHANNEL_NAME = 'tot_auth_sync';

// ---------------------------------------------------------------------------
// STATE
// ---------------------------------------------------------------------------

let currentTokens: AuthTokens | null = null;
let refreshTimer: number | null = null;
let inFlightRefresh: Promise<AuthTokens | null> | null = null;

// ---------------------------------------------------------------------------
// CROSS-TAB COORDINATION
// ---------------------------------------------------------------------------

/**
 * BroadcastChannel for cross-tab token synchronization.
 * Falls back to localStorage events if BroadcastChannel is not supported.
 */
let broadcastChannel: BroadcastChannel | null = null;

try {
  broadcastChannel = new BroadcastChannel(BROADCAST_CHANNEL_NAME);
  broadcastChannel.onmessage = (event) => {
    const { type, tokens } = event.data;
    if (type === 'TOKEN_REFRESHED' && tokens) {
      // Another tab refreshed tokens, adopt them
      storeTokens(tokens);
      scheduleTokenRefresh(tokens);
    } else if (type === 'TOKEN_CLEARED') {
      // Another tab cleared tokens
      clearStoredTokens();
    }
  };
} catch {
  // BroadcastChannel not supported, rely on localStorage events
  broadcastChannel = null;
}

/**
 * Listen for localStorage changes from other tabs (fallback)
 */
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (event) => {
    if (event.key === TOKEN_KEY) {
      if (event.newValue) {
        try {
          const tokens = JSON.parse(event.newValue) as AuthTokens;
          if (!isTokenExpired(tokens.accessToken)) {
            currentTokens = tokens;
            scheduleTokenRefresh(tokens);
          }
        } catch {
          // Invalid JSON, ignore
        }
      } else {
        currentTokens = null;
        if (refreshTimer !== null) {
          clearTimeout(refreshTimer);
          refreshTimer = null;
        }
      }
    }
  });
}

function broadcastTokenRefresh(tokens: AuthTokens): void {
  if (broadcastChannel) {
    broadcastChannel.postMessage({
      type: 'TOKEN_REFRESHED',
      tokens,
    });
  }
}

function broadcastTokenClear(): void {
  if (broadcastChannel) {
    broadcastChannel.postMessage({
      type: 'TOKEN_CLEARED',
    });
  }
}

// ---------------------------------------------------------------------------
// TOKEN UTILITIES
// ---------------------------------------------------------------------------

function isTokenExpired(token: string): boolean {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const expiry = payload.exp * 1000;
    return Date.now() >= expiry;
  } catch {
    return true;
  }
}

function getTokenExpiry(token: string): number {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.exp * 1000;
  } catch {
    return 0;
  }
}

function storeTokens(tokens: AuthTokens): void {
  currentTokens = tokens;
  try {
    localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
  } catch {
    // localStorage might be full or unavailable
  }
}

function clearStoredTokens(): void {
  currentTokens = null;
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Ignore errors
  }
  if (refreshTimer !== null) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }
}

function loadStoredTokens(): AuthTokens | null {
  try {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (stored) {
      const tokens = JSON.parse(stored) as AuthTokens;
      if (!isTokenExpired(tokens.accessToken)) {
        currentTokens = tokens;
        return tokens;
      }
    }
  } catch {
    // Ignore parse errors
  }
  return null;
}

// ---------------------------------------------------------------------------
// TOKEN REFRESH
// ---------------------------------------------------------------------------

function scheduleTokenRefresh(tokens: AuthTokens): void {
  if (refreshTimer !== null) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }

  const expiresIn = tokens.expiresIn;
  const refreshIn = Math.max((expiresIn - REFRESH_THRESHOLD) * 1000, 0);

  refreshTimer = window.setTimeout(async () => {
    refreshTimer = null;
    const newTokens = await refreshTokens();
    if (newTokens) {
      scheduleTokenRefresh(newTokens);
    }
    // Refresh failed, will retry on next API call
  }, refreshIn);
}

/**
 * Refresh tokens with cross-tab coordination.
 * Concurrent calls in the same tab share one in-flight refresh request.
 * Cross-tab coordination ensures only one tab performs the network refresh.
 */
export async function refreshTokens(): Promise<AuthTokens | null> {
  // If there's already an in-flight refresh, wait for it
  if (inFlightRefresh) {
    return inFlightRefresh;
  }

  // Create new refresh promise
  inFlightRefresh = performTokenRefresh();

  try {
    const result = await inFlightRefresh;
    return result;
  } finally {
    inFlightRefresh = null;
  }
}

async function performTokenRefresh(): Promise<AuthTokens | null> {
  const tokens = currentTokens || loadStoredTokens();
  if (!tokens?.refreshToken) return null;

  try {
    const response = await post<{ tokens: AuthTokens }>('/auth/refresh', {
      refreshToken: tokens.refreshToken,
    });

    const newTokens = response.data.tokens;
    storeTokens(newTokens);
    scheduleTokenRefresh(newTokens);

    // Broadcast to other tabs
    broadcastTokenRefresh(newTokens);

    return newTokens;
  } catch {
    // Refresh failed - don't clear tokens if another tab might have succeeded
    // Only clear if we're sure the refresh token is invalid
    return null;
  }
}

// ---------------------------------------------------------------------------
// AUTH OPERATIONS
// ---------------------------------------------------------------------------

export async function login(request: LoginRequest): Promise<AuthTokens> {
  const response = await post<{ tokens: AuthTokens; user: User }>('/auth/login', request);

  storeTokens(response.data.tokens);
  scheduleTokenRefresh(response.data.tokens);
  broadcastTokenRefresh(response.data.tokens);

  return response.data.tokens;
}

export async function register(request: RegisterRequest): Promise<AuthTokens> {
  const response = await post<{ tokens: AuthTokens; user: User }>('/auth/register', request);

  storeTokens(response.data.tokens);
  scheduleTokenRefresh(response.data.tokens);
  broadcastTokenRefresh(response.data.tokens);

  return response.data.tokens;
}

export async function logout(): Promise<void> {
  try {
    await post('/auth/logout', {});
  } catch {
    // Ignore logout errors
  }

  clearStoredTokens();
  broadcastTokenClear();

  if (refreshTimer !== null) {
    clearTimeout(refreshTimer);
    refreshTimer = null;
  }
}

export async function getCurrentUser(): Promise<User | null> {
  try {
    // Try to restore session from stored tokens
    const tokens = loadStoredTokens();
    if (tokens && !isTokenExpired(tokens.accessToken)) {
      const response = await get<{ user: User }>('/auth/me');
      return response.data.user;
    }

    // Token might be expired or invalid
    const refreshed = await refreshTokens();
    if (refreshed) {
      const response = await get<{ user: User }>('/auth/me');
      return response.data.user;
    }
  } catch {
    // Token invalid or network error
  }
  return null;
}

export async function updateProfile(updates: Partial<User>): Promise<User> {
  const response = await put<{ user: User }>('/auth/profile', updates);
  return response.data.user;
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await post('/auth/change-password', { currentPassword, newPassword });
}

export async function enableMFA(): Promise<{ secret: string; qrCode: string }> {
  const response = await post<{ secret: string; qrCode: string }>('/auth/mfa/enable', {});
  return response.data;
}

export async function verifyMFA(code: string): Promise<void> {
  await post('/auth/mfa/verify', { code });
}

export async function disableMFA(code: string): Promise<void> {
  await post('/auth/mfa/disable', { code });
}

export async function generateBackupCodes(): Promise<string[]> {
  const response = await post<{ codes: string[] }>('/auth/mfa/backup-codes', {});
  return response.data.codes;
}

export async function forgotPassword(email: string): Promise<void> {
  await post('/auth/forgot-password', { email });
}

export async function resetPassword(token: string, newPassword: string): Promise<void> {
  await post('/auth/reset-password/confirm', { token, newPassword });
}

export async function verifyEmail(token: string): Promise<void> {
  await post('/auth/verify-email', { token });
}

export async function resendVerification(): Promise<void> {
  await post('/auth/resend-verification', {});
}

// ---------------------------------------------------------------------------
// OAUTH
// ---------------------------------------------------------------------------

export function getOAuthUrl(provider: string, redirectUri?: string): string {
  const params = new URLSearchParams();
  if (redirectUri) params.set('redirect_uri', redirectUri);
  return `/auth/oauth/${provider}?${params.toString()}`;
}

export async function handleOAuthCallback(code: string, state: string): Promise<AuthTokens> {
  const response = await post<{ tokens: AuthTokens; user: User }>('/auth/oauth/callback', {
    code,
    state,
  });

  storeTokens(response.data.tokens);
  scheduleTokenRefresh(response.data.tokens);
  broadcastTokenRefresh(response.data.tokens);

  return response.data.tokens;
}

// ---------------------------------------------------------------------------
// SESSION
// ---------------------------------------------------------------------------

export function getAccessToken(): string | null {
  return currentTokens?.accessToken || null;
}

export function isAuthenticated(): boolean {
  const tokens = currentTokens || loadStoredTokens();
  return tokens !== null && !isTokenExpired(tokens.accessToken);
}

export function getAuthHeaders(): Record<string, string> {
  const token = getAccessToken();
  if (token) {
    return {
      Authorization: `Bearer ${token}`,
    };
  }
  return {};
}
