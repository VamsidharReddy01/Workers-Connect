import type {
  AuthResponse,
  Booking,
  BookingStatus,
  CategorySummary,
  Conversation,
  Message,
  SignupPayload,
  SupportTicket,
  User,
  WorkerDashboardSummary,
  WorkerProfile,
} from './types';

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, '') ??
  'http://127.0.0.1:8000';

type ApiErrorPayload = {
  detail?: string;
  error?: string;
  errors?: Record<string, unknown>;
};

function firstError(errors: Record<string, unknown>): string {
  for (const value of Object.values(errors)) {
    if (Array.isArray(value) && value.length > 0) return String(value[0]);
    if (typeof value === 'string') return value;
    if (value && typeof value === 'object') {
      return firstError(value as Record<string, unknown>);
    }
  }
  return 'Please check your input and try again.';
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  headers.set('Accept', 'application/json');
  if (token) headers.set('Authorization', `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
    });
  } catch (error) {
    if (error instanceof TypeError) {
      throw new Error(
        `Cannot reach the backend at ${API_BASE_URL}. Start Django with "python manage.py runserver 127.0.0.1:8000" and try again.`,
      );
    }
    throw error;
  }

  const data = (await response.json().catch(() => ({}))) as ApiErrorPayload;
  if (!response.ok) {
    throw new Error(
      data.errors ? firstError(data.errors) : data.detail ?? data.error ?? 'Request failed.',
    );
  }

  return data as T;
}

export const api = {
  sendSignupOtp(email: string) {
    return request<{ message: string }>('/api/auth/signup/send-otp/', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  },
  geocode(data: { latitude?: number; longitude?: number; location_name?: string }) {
    return request<{ latitude: number | null; longitude: number | null; location_name: string }>(
      '/api/auth/geocode/',
      { method: 'POST', body: JSON.stringify(data) },
    );
  },
  signup(data: SignupPayload) {
    const endpoint = data.role === 'worker' ? '/api/auth/worker-signup/' : '/api/auth/customer-signup/';
    return request<AuthResponse>(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },
  workerSignup(data: SignupPayload) {
    return request<AuthResponse>('/api/auth/worker-signup/', {
      method: 'POST',
      body: JSON.stringify({ ...data, role: 'worker' }),
    });
  },
  customerSignup(data: SignupPayload) {
    return request<AuthResponse>('/api/auth/customer-signup/', {
      method: 'POST',
      body: JSON.stringify({ ...data, role: 'customer' }),
    });
  },
  login(email: string, password: string) {
    return request<AuthResponse>('/api/auth/login/', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },
  refresh(refresh: string) {
    return request<{ access: string }>('/api/auth/token/refresh/', {
      method: 'POST',
      body: JSON.stringify({ refresh }),
    });
  },
  logout(token: string, refresh: string) {
    return request<{ message: string }>(
      '/api/auth/logout/',
      { method: 'POST', body: JSON.stringify({ refresh }) },
      token,
    );
  },
  profile(token: string) {
    return request<User>('/api/auth/profile/', {}, token);
  },
  updateProfile(token: string, data: Partial<User>) {
    return request<User>(
      '/api/auth/profile/',
      { method: 'PATCH', body: JSON.stringify(data) },
      token,
    );
  },
  updateProfileForm(token: string, data: FormData) {
    return request<User>(
      '/api/auth/profile/',
      { method: 'PATCH', body: data },
      token,
    );
  },
  changePassword(
    token: string,
    oldPassword: string,
    newPassword: string,
    confirmPassword: string,
  ) {
    return request<{ message: string }>(
      '/api/auth/change-password/',
      {
        method: 'POST',
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword,
          confirm_password: confirmPassword,
        }),
      },
      token,
    );
  },
  supportTickets(token: string) {
    return request<{ list: SupportTicket[] }>('/api/auth/support/tickets/', {}, token);
  },
  createSupportTicket(token: string, subject: string, message: string) {
    return request<SupportTicket>(
      '/api/auth/support/tickets/',
      { method: 'POST', body: JSON.stringify({ subject, message }) },
      token,
    );
  },
  categories() {
    return request<{ list: CategorySummary[] }>('/api/workers/categories/');
  },
  jobCategories() {
    return request<{ list: string[] }>('/api/workers/job-categories/');
  },
  nearbyWorkers(
    params: {
      category?: string;
      search?: string;
      availableOnly?: boolean;
      lat?: number | null;
      lng?: number | null;
      radius?: number | null;
    } = {},
    token?: string | null,
  ) {
    const query = new URLSearchParams();
    if (params.category) query.set('category', params.category);
    if (params.search) query.set('search', params.search);
    if (params.availableOnly) query.set('available_only', 'true');
    if (params.lat != null) query.set('lat', String(params.lat));
    if (params.lng != null) query.set('lng', String(params.lng));
    if (params.radius != null) query.set('radius', String(params.radius));
    const suffix = query.toString() ? `?${query}` : '';
    return request<{ list: WorkerProfile[] }>(`/api/workers/nearby/${suffix}`, {}, token);
  },
  workerDetail(workerId: number) {
    return request<WorkerProfile>(`/api/workers/${workerId}/`);
  },
  createBooking(
    token: string,
    data: {
      worker_id: number;
      service_category: string;
      description: string;
      address: string;
      service_latitude?: number | string | null;
      service_longitude?: number | string | null;
      location_permission_granted?: boolean;
      service_location_source?: 'saved' | 'gps' | 'manual' | null;
      scheduled_at: string;
      total_amount: string;
    },
  ) {
    return request<Booking>(
      '/api/workers/bookings/create/',
      { method: 'POST', body: JSON.stringify(data) },
      token,
    );
  },
  customerBookings(token: string, status?: BookingStatus) {
    const suffix = status ? `?status=${encodeURIComponent(status)}` : '';
    return request<{ list: Booking[] }>(`/api/workers/bookings/my/${suffix}`, {}, token);
  },
  createReview(token: string, bookingId: number, rating: number, feedback: string) {
    return request<{ id: number }>(
      `/api/workers/bookings/${bookingId}/review/`,
      { method: 'POST', body: JSON.stringify({ rating, feedback }) },
      token,
    );
  },
  workerProfile(token: string) {
    return request<WorkerProfile>('/api/workers/profile/', {}, token);
  },
  saveWorkerProfile(token: string, data: Record<string, unknown>) {
    return request<WorkerProfile>(
      '/api/workers/profile/',
      { method: 'POST', body: JSON.stringify(data) },
      token,
    );
  },
  workerDashboard(token: string) {
    return request<WorkerDashboardSummary>('/api/workers/dashboard/', {}, token);
  },
  workerBookings(token: string, status?: BookingStatus) {
    const suffix = status ? `?status=${encodeURIComponent(status)}` : '';
    return request<{ list: Booking[] }>(`/api/workers/bookings/${suffix}`, {}, token);
  },
  updateBookingStatus(token: string, bookingId: number, status: BookingStatus) {
    return request<Booking>(
      `/api/workers/bookings/${bookingId}/status/`,
      { method: 'PATCH', body: JSON.stringify({ status }) },
      token,
    );
  },
  updateAvailability(token: string, isOnline: boolean) {
    return request<WorkerProfile>(
      '/api/workers/availability/',
      { method: 'PATCH', body: JSON.stringify({ is_online: isOnline }) },
      token,
    );
  },
  uploadWorkImages(token: string, formData: FormData) {
    return request<{ list: WorkerProfile['work_images'] }>(
      '/api/workers/profile/work-images/',
      { method: 'POST', body: formData },
      token,
    );
  },
  deleteWorkImage(token: string, imageId: number) {
    return request<void>(
      `/api/workers/profile/work-images/${imageId}/`,
      { method: 'DELETE' },
      token,
    );
  },
  conversations(token: string) {
    return request<{ list: Conversation[] }>('/api/workers/conversations/', {}, token);
  },
  messages(token: string, conversationId: number) {
    return request<{ list: Message[] }>(
      `/api/workers/conversations/${conversationId}/messages/`,
      {},
      token,
    );
  },
  sendMessage(token: string, conversationId: number, text: string) {
    return request<Message>(
      `/api/workers/conversations/${conversationId}/messages/`,
      { method: 'POST', body: JSON.stringify({ text }) },
      token,
    );
  },
};
