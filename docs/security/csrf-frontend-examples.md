# CSRF Protection - Frontend Integration Examples

This guide provides complete, production-ready code examples for integrating CSRF protection in various frontend frameworks and libraries.

## Table of Contents

- [React / Next.js](#react--nextjs)
- [Vue.js](#vuejs)
- [Angular](#angular)
- [Vanilla JavaScript](#vanilla-javascript)
- [jQuery](#jquery)
- [Axios Configuration](#axios-configuration)
- [Testing Examples](#testing-examples)

---

## React / Next.js

### Custom Hook for CSRF Token

```typescript
// hooks/useCsrfToken.ts
import { useState, useEffect } from 'react';

interface CsrfTokenResponse {
  csrf_token: string;
  message: string;
}

export function useCsrfToken(): string | null {
  const [csrfToken, setCsrfToken] = useState<string | null>(null);

  useEffect(() => {
    async function fetchCsrfToken() {
      try {
        const response = await fetch('/api/security/csrf-token', {
          credentials: 'include', // Important: send cookies
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data: CsrfTokenResponse = await response.json();
        setCsrfToken(data.csrf_token);
      } catch (error) {
        console.error('Failed to fetch CSRF token:', error);
        setCsrfToken(null);
      }
    }

    fetchCsrfToken();
  }, []);

  return csrfToken;
}
```

### API Client with CSRF Support

```typescript
// lib/api-client.ts
class ApiClient {
  private csrfToken: string | null = null;
  private baseUrl: string;

  constructor(baseUrl: string = '/api') {
    this.baseUrl = baseUrl;
    this.initializeCsrfToken();
  }

  private async initializeCsrfToken(): Promise<void> {
    try {
      const response = await fetch(`${this.baseUrl}/security/csrf-token`, {
        credentials: 'include',
      });
      const data = await response.json();
      this.csrfToken = data.csrf_token;
    } catch (error) {
      console.error('Failed to initialize CSRF token:', error);
    }
  }

  private getHeaders(includeAuth: boolean = false): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    // Add CSRF token for state-changing requests
    if (this.csrfToken) {
      headers['X-CSRF-Token'] = this.csrfToken;
    }

    // Add authentication header if available
    if (includeAuth) {
      const token = localStorage.getItem('access_token');
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    return headers;
  }

  async get<T>(path: string, authenticated: boolean = false): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'GET',
      headers: this.getHeaders(authenticated),
      credentials: 'include',
    });

    if (!response.ok) {
      throw await this.handleError(response);
    }

    return response.json();
  }

  async post<T>(
    path: string,
    data: any,
    authenticated: boolean = false
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: this.getHeaders(authenticated),
      credentials: 'include',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      // If CSRF token invalid, refresh and retry once
      if (response.status === 403) {
        const error = await response.json();
        if (
          error.error_type === 'csrf_token_invalid' ||
          error.error_type === 'csrf_token_missing'
        ) {
          await this.initializeCsrfToken();
          return this.post<T>(path, data, authenticated);
        }
      }

      throw await this.handleError(response);
    }

    return response.json();
  }

  async put<T>(
    path: string,
    data: any,
    authenticated: boolean = false
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'PUT',
      headers: this.getHeaders(authenticated),
      credentials: 'include',
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw await this.handleError(response);
    }

    return response.json();
  }

  async delete<T>(path: string, authenticated: boolean = false): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: 'DELETE',
      headers: this.getHeaders(authenticated),
      credentials: 'include',
    });

    if (!response.ok) {
      throw await this.handleError(response);
    }

    return response.json();
  }

  private async handleError(response: Response): Promise<Error> {
    try {
      const error = await response.json();
      return new Error(error.detail || error.message || 'Request failed');
    } catch {
      return new Error(`Request failed with status ${response.status}`);
    }
  }

  async refreshCsrfToken(): Promise<void> {
    await this.initializeCsrfToken();
  }
}

// Export singleton instance
export const apiClient = new ApiClient();
```

### Login Component Example

```tsx
// components/LoginForm.tsx
import React, { useState } from 'react';
import { useCsrfToken } from '@/hooks/useCsrfToken';
import { apiClient } from '@/lib/api-client';

interface LoginFormData {
  email: string;
  password: string;
}

export function LoginForm() {
  const csrfToken = useCsrfToken();
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    if (!csrfToken) {
      setError('CSRF token not available. Please refresh the page.');
      setLoading(false);
      return;
    }

    try {
      const response = await apiClient.post('/auth/login', formData);

      // Store access token
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('refresh_token', response.refresh_token);

      // Refresh CSRF token after login (it's rotated)
      await apiClient.refreshCsrfToken();

      // Redirect to dashboard
      window.location.href = '/dashboard';
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="email" className="block text-sm font-medium">
          Email
        </label>
        <input
          id="email"
          type="email"
          value={formData.email}
          onChange={(e) => setFormData({ ...formData, email: e.target.value })}
          required
          className="mt-1 block w-full rounded border px-3 py-2"
        />
      </div>

      <div>
        <label htmlFor="password" className="block text-sm font-medium">
          Password
        </label>
        <input
          id="password"
          type="password"
          value={formData.password}
          onChange={(e) =>
            setFormData({ ...formData, password: e.target.value })
          }
          required
          className="mt-1 block w-full rounded border px-3 py-2"
        />
      </div>

      {error && (
        <div className="rounded bg-red-50 p-3 text-sm text-red-800">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading || !csrfToken}
        className="w-full rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 disabled:bg-gray-400"
      >
        {loading ? 'Logging in...' : 'Login'}
      </button>
    </form>
  );
}
```

---

## Vue.js

### CSRF Plugin

```javascript
// plugins/csrf.js
export default {
  install: (app) => {
    let csrfToken = null;

    // Fetch CSRF token on plugin install
    const fetchCsrfToken = async () => {
      try {
        const response = await fetch('/api/security/csrf-token', {
          credentials: 'include',
        });
        const data = await response.json();
        csrfToken = data.csrf_token;
        return csrfToken;
      } catch (error) {
        console.error('Failed to fetch CSRF token:', error);
        return null;
      }
    };

    // Initialize token
    fetchCsrfToken();

    // Provide CSRF token to all components
    app.provide('csrfToken', {
      get: () => csrfToken,
      refresh: fetchCsrfToken,
    });

    // Add global request helper
    app.config.globalProperties.$apiPost = async (url, data) => {
      if (!csrfToken) {
        await fetchCsrfToken();
      }

      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRF-Token': csrfToken,
        },
        credentials: 'include',
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return response.json();
    };
  },
};
```

### Composable for CSRF Token

```javascript
// composables/useCsrf.js
import { ref, onMounted } from 'vue';

export function useCsrf() {
  const csrfToken = ref(null);
  const loading = ref(false);
  const error = ref(null);

  const fetchCsrfToken = async () => {
    loading.value = true;
    error.value = null;

    try {
      const response = await fetch('/api/security/csrf-token', {
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      csrfToken.value = data.csrf_token;
    } catch (err) {
      error.value = err.message;
      console.error('Failed to fetch CSRF token:', err);
    } finally {
      loading.value = false;
    }
  };

  const makeRequest = async (url, options = {}) => {
    if (!csrfToken.value) {
      await fetchCsrfToken();
    }

    const method = options.method || 'GET';
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add CSRF token for state-changing requests
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase())) {
      headers['X-CSRF-Token'] = csrfToken.value;
    }

    const response = await fetch(url, {
      ...options,
      method,
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  };

  onMounted(() => {
    fetchCsrfToken();
  });

  return {
    csrfToken,
    loading,
    error,
    fetchCsrfToken,
    makeRequest,
  };
}
```

### Vue Component Example

```vue
<!-- components/RegistrationForm.vue -->
<template>
  <form @submit.prevent="handleSubmit" class="space-y-4">
    <div>
      <label for="email">Email</label>
      <input
        id="email"
        v-model="form.email"
        type="email"
        required
        class="w-full border rounded px-3 py-2"
      />
    </div>

    <div>
      <label for="password">Password</label>
      <input
        id="password"
        v-model="form.password"
        type="password"
        required
        class="w-full border rounded px-3 py-2"
      />
    </div>

    <div v-if="error" class="text-red-600">{{ error }}</div>

    <button
      type="submit"
      :disabled="isSubmitting || !csrfToken"
      class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
    >
      {{ isSubmitting ? 'Registering...' : 'Register' }}
    </button>
  </form>
</template>

<script setup>
import { ref } from 'vue';
import { useCsrf } from '@/composables/useCsrf';

const { csrfToken, makeRequest } = useCsrf();

const form = ref({
  email: '',
  password: '',
  first_name: '',
  last_name: '',
});

const error = ref(null);
const isSubmitting = ref(false);

const handleSubmit = async () => {
  error.value = null;
  isSubmitting.value = true;

  try {
    const response = await makeRequest('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(form.value),
    });

    console.log('Registration successful:', response);
    // Redirect or show success message
  } catch (err) {
    error.value = err.message;
  } finally {
    isSubmitting.value = false;
  }
};
</script>
```

---

## Angular

### CSRF Interceptor

```typescript
// interceptors/csrf.interceptor.ts
import { Injectable } from '@angular/core';
import {
  HttpInterceptor,
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpErrorResponse,
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';
import { CsrfService } from '../services/csrf.service';

@Injectable()
export class CsrfInterceptor implements HttpInterceptor {
  constructor(private csrfService: CsrfService) {}

  intercept(
    request: HttpRequest<any>,
    next: HttpHandler
  ): Observable<HttpEvent<any>> {
    // Only add CSRF token to state-changing requests
    if (this.isStateMutating(request.method)) {
      const csrfToken = this.csrfService.getToken();

      if (csrfToken) {
        request = request.clone({
          setHeaders: {
            'X-CSRF-Token': csrfToken,
          },
          withCredentials: true,
        });
      }
    }

    return next.handle(request).pipe(
      catchError((error: HttpErrorResponse) => {
        // If CSRF token invalid, refresh and retry once
        if (
          error.status === 403 &&
          error.error?.error_type?.includes('csrf')
        ) {
          return this.csrfService.refreshToken().pipe(
            switchMap(() => {
              const newToken = this.csrfService.getToken();
              const retryRequest = request.clone({
                setHeaders: {
                  'X-CSRF-Token': newToken || '',
                },
                withCredentials: true,
              });
              return next.handle(retryRequest);
            })
          );
        }

        return throwError(() => error);
      })
    );
  }

  private isStateMutating(method: string): boolean {
    return ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase());
  }
}
```

### CSRF Service

```typescript
// services/csrf.service.ts
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';

interface CsrfTokenResponse {
  csrf_token: string;
  message: string;
}

@Injectable({
  providedIn: 'root',
})
export class CsrfService {
  private csrfToken$ = new BehaviorSubject<string | null>(null);

  constructor(private http: HttpClient) {
    this.initializeToken();
  }

  private initializeToken(): void {
    this.http
      .get<CsrfTokenResponse>('/api/security/csrf-token', {
        withCredentials: true,
      })
      .subscribe({
        next: (response) => this.csrfToken$.next(response.csrf_token),
        error: (error) => console.error('Failed to fetch CSRF token:', error),
      });
  }

  getToken(): string | null {
    return this.csrfToken$.value;
  }

  getToken$(): Observable<string | null> {
    return this.csrfToken$.asObservable();
  }

  refreshToken(): Observable<CsrfTokenResponse> {
    return this.http
      .get<CsrfTokenResponse>('/api/security/csrf-token', {
        withCredentials: true,
      })
      .pipe(tap((response) => this.csrfToken$.next(response.csrf_token)));
  }
}
```

### Module Configuration

```typescript
// app.module.ts
import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { CsrfInterceptor } from './interceptors/csrf.interceptor';
import { CsrfService } from './services/csrf.service';

@NgModule({
  declarations: [
    // Your components
  ],
  imports: [BrowserModule, HttpClientModule],
  providers: [
    CsrfService,
    {
      provide: HTTP_INTERCEPTORS,
      useClass: CsrfInterceptor,
      multi: true,
    },
  ],
  bootstrap: [AppComponent],
})
export class AppModule {}
```

---

## Vanilla JavaScript

### Simple CSRF Helper

```javascript
// csrf-helper.js
class CsrfHelper {
  constructor() {
    this.token = null;
    this.isInitialized = false;
  }

  async initialize() {
    if (this.isInitialized) return;

    try {
      const response = await fetch('/api/security/csrf-token', {
        credentials: 'include',
      });
      const data = await response.json();
      this.token = data.csrf_token;
      this.isInitialized = true;
    } catch (error) {
      console.error('Failed to initialize CSRF token:', error);
    }
  }

  getToken() {
    return this.token;
  }

  async request(url, options = {}) {
    if (!this.isInitialized) {
      await this.initialize();
    }

    const method = options.method || 'GET';
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    };

    // Add CSRF token for state-changing requests
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase())) {
      headers['X-CSRF-Token'] = this.token;
    }

    const response = await fetch(url, {
      ...options,
      method,
      headers,
      credentials: 'include',
    });

    if (!response.ok) {
      // Handle CSRF token refresh
      if (response.status === 403) {
        const error = await response.json();
        if (error.error_type?.includes('csrf')) {
          // Refresh token and retry
          this.isInitialized = false;
          await this.initialize();
          return this.request(url, options);
        }
      }

      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }
}

// Export singleton
const csrf = new CsrfHelper();
export default csrf;
```

### Usage Example

```javascript
// app.js
import csrf from './csrf-helper.js';

// Initialize on page load
document.addEventListener('DOMContentLoaded', async () => {
  await csrf.initialize();

  // Login form
  document.getElementById('login-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    try {
      const response = await csrf.request('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });

      console.log('Login successful:', response);
      // Refresh CSRF token after login
      await csrf.initialize();

      // Redirect to dashboard
      window.location.href = '/dashboard';
    } catch (error) {
      console.error('Login failed:', error);
      document.getElementById('error').textContent = error.message;
    }
  });
});
```

---

## jQuery

### jQuery CSRF Plugin

```javascript
// jquery.csrf.js
(function ($) {
  $.csrf = {
    token: null,

    init: function () {
      return $.ajax({
        url: '/api/security/csrf-token',
        method: 'GET',
        xhrFields: {
          withCredentials: true,
        },
        success: function (data) {
          $.csrf.token = data.csrf_token;
        },
        error: function (error) {
          console.error('Failed to fetch CSRF token:', error);
        },
      });
    },

    getToken: function () {
      return this.token;
    },

    ajaxSetup: function () {
      $.ajaxSetup({
        beforeSend: function (xhr, settings) {
          // Add CSRF token to state-changing requests
          if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(settings.type)) {
            xhr.setRequestHeader('X-CSRF-Token', $.csrf.token);
          }
        },
        xhrFields: {
          withCredentials: true,
        },
      });
    },
  };
})(jQuery);

// Initialize CSRF on document ready
$(document).ready(function () {
  $.csrf.init().then(function () {
    $.csrf.ajaxSetup();
  });
});
```

### jQuery Usage Example

```javascript
// login.js
$(document).ready(function () {
  $('#login-form').on('submit', function (e) {
    e.preventDefault();

    const email = $('#email').val();
    const password = $('#password').val();

    $.ajax({
      url: '/api/auth/login',
      method: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({ email, password }),
      success: function (response) {
        console.log('Login successful:', response);

        // Refresh CSRF token after login
        $.csrf.init();

        // Redirect
        window.location.href = '/dashboard';
      },
      error: function (xhr) {
        const error = xhr.responseJSON?.detail || 'Login failed';
        $('#error').text(error);
      },
    });
  });
});
```

---

## Axios Configuration

### Axios Instance with CSRF

```javascript
// lib/axios.js
import axios from 'axios';

// Create axios instance
const api = axios.create({
  baseURL: '/api',
  withCredentials: true, // Important: send cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

// CSRF token storage
let csrfToken = null;

// Fetch CSRF token
async function fetchCsrfToken() {
  try {
    const response = await api.get('/security/csrf-token');
    csrfToken = response.data.csrf_token;
    return csrfToken;
  } catch (error) {
    console.error('Failed to fetch CSRF token:', error);
    return null;
  }
}

// Initialize token
fetchCsrfToken();

// Request interceptor - add CSRF token
api.interceptors.request.use(
  (config) => {
    // Add CSRF token for state-changing requests
    if (['post', 'put', 'delete', 'patch'].includes(config.method)) {
      config.headers['X-CSRF-Token'] = csrfToken;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle CSRF errors
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If CSRF token invalid, refresh and retry
    if (
      error.response?.status === 403 &&
      error.response?.data?.error_type?.includes('csrf') &&
      !originalRequest._retry
    ) {
      originalRequest._retry = true;

      // Refresh token
      await fetchCsrfToken();

      // Retry original request with new token
      originalRequest.headers['X-CSRF-Token'] = csrfToken;
      return api(originalRequest);
    }

    return Promise.reject(error);
  }
);

// Export API instance and helper
export { api, fetchCsrfToken };
export default api;
```

---

## Testing Examples

### Jest Test Example

```javascript
// __tests__/csrf.test.js
import { apiClient } from '../lib/api-client';

describe('CSRF Protection', () => {
  beforeEach(() => {
    // Mock fetch
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  test('should fetch CSRF token on initialization', async () => {
    const mockToken = 'test-csrf-token-123';

    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ csrf_token: mockToken }),
    });

    const client = new ApiClient();
    await new Promise((resolve) => setTimeout(resolve, 100)); // Wait for init

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/csrf-token'),
      expect.objectContaining({ credentials: 'include' })
    );
  });

  test('should include CSRF token in POST request', async () => {
    const mockToken = 'test-csrf-token-456';

    // Mock token fetch
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ csrf_token: mockToken }),
    });

    // Mock POST request
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    });

    const client = new ApiClient();
    await new Promise((resolve) => setTimeout(resolve, 100));

    await client.post('/test', { data: 'test' });

    const postCall = global.fetch.mock.calls[1];
    expect(postCall[1].headers['X-CSRF-Token']).toBe(mockToken);
  });

  test('should refresh token and retry on CSRF error', async () => {
    const oldToken = 'old-token';
    const newToken = 'new-token';

    // Mock initial token fetch
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ csrf_token: oldToken }),
    });

    // Mock failed POST (CSRF error)
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 403,
      json: async () => ({
        error_type: 'csrf_token_invalid',
        detail: 'CSRF token invalid',
      }),
    });

    // Mock token refresh
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ csrf_token: newToken }),
    });

    // Mock retry POST (success)
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    });

    const client = new ApiClient();
    await new Promise((resolve) => setTimeout(resolve, 100));

    const result = await client.post('/test', { data: 'test' });

    expect(result).toEqual({ success: true });
    expect(global.fetch).toHaveBeenCalledTimes(4); // init + failed post + refresh + retry
  });
});
```

---

## Best Practices Summary

1. **Always use `credentials: 'include'`** to send cookies with requests
2. **Fetch token on app initialization** before making any state-changing requests
3. **Refresh token after login** as it gets rotated for security
4. **Handle 403 CSRF errors** by refreshing token and retrying request
5. **Store token in memory** (not localStorage) for better security
6. **Use interceptors/middleware** for automatic token inclusion
7. **Test CSRF integration** to ensure it works correctly

---

## Troubleshooting

### Token Not Available
```javascript
// Always check token availability before request
if (!csrfToken) {
  console.warn('CSRF token not available, fetching...');
  await fetchCsrfToken();
}
```

### CORS Issues
```javascript
// Ensure credentials are included
fetch(url, {
  credentials: 'include', // Required for cookies
  mode: 'cors',
});
```

### Token Mismatch After Login
```javascript
// Refresh token after login
async function login(email, password) {
  const response = await api.post('/auth/login', { email, password });

  // Token is rotated after login, fetch new one
  await fetchCsrfToken();

  return response;
}
```

---

**Last Updated:** 2025-11-10
**Maintained By:** Frontend Team
