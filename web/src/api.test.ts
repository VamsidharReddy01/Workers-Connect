import { afterEach, describe, expect, it, vi } from 'vitest';
import { api } from './api';

const originalFetch = globalThis.fetch;

afterEach(() => {
  globalThis.fetch = originalFetch;
  vi.restoreAllMocks();
});

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  return new Response(JSON.stringify(body), {
    headers: { 'Content-Type': 'application/json' },
    status: 200,
    ...init,
  });
}

describe('api client', () => {
  it('sends login payload to the auth endpoint', async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      jsonResponse({
        access: 'access-token',
        refresh: 'refresh-token',
        user: { id: 1, username: 'Demo', email: 'demo@example.com', role: 'customer' },
      }),
    );
    globalThis.fetch = fetchMock;

    const result = await api.login('demo@example.com', 'password123');

    expect(result.access).toBe('access-token');
    expect(fetchMock).toHaveBeenCalledWith(
      'http://127.0.0.1:8000/api/auth/login/',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ email: 'demo@example.com', password: 'password123' }),
      }),
    );
  });

  it('adds bearer authorization to protected requests', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ list: [] }));
    globalThis.fetch = fetchMock;

    await api.supportTickets('secure-token');

    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get('Authorization')).toBe('Bearer secure-token');
    expect(headers.get('Accept')).toBe('application/json');
  });

  it('does not set JSON content type for FormData uploads', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ list: [] }, { status: 201 }));
    globalThis.fetch = fetchMock;
    const formData = new FormData();
    formData.append('images', new File(['image'], 'work.png', { type: 'image/png' }));

    await api.uploadWorkImages('secure-token', formData);

    const headers = fetchMock.mock.calls[0][1].headers as Headers;
    expect(headers.get('Content-Type')).toBeNull();
  });

  it('surfaces backend validation errors', async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(
      jsonResponse(
        { errors: { email: ['A user with this email already exists.'] } },
        { status: 400 },
      ),
    );

    await expect(api.sendSignupOtp('used@example.com')).rejects.toThrow(
      'A user with this email already exists.',
    );
  });

  it('explains backend connectivity failures', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(api.login('demo@example.com', 'password123')).rejects.toThrow(
      'Cannot reach the backend at http://127.0.0.1:8000.',
    );
  });
});
