import {
  BriefcaseBusiness,
  CalendarDays,
  CheckCircle2,
  Clock3,
  DollarSign,
  Home,
  ImagePlus,
  LayoutDashboard,
  LogOut,
  Mail,
  MapPin,
  MessageCircle,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Star,
  Trash2,
  UploadCloud,
  UserRound,
  Wrench,
} from 'lucide-react';
import type { ReactNode } from 'react';
import { FormEvent, useCallback, useEffect, useMemo, useState } from 'react';
import {
  BrowserRouter,
  Navigate,
  NavLink,
  Route,
  Routes,
  Link,
  useNavigate,
} from 'react-router-dom';
import { api } from './api';
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
  Coordinates,
} from './types';

const storedAccessKey = 'workersbridge.access';
const storedRefreshKey = 'workersbridge.refresh';

const bookingStatuses: BookingStatus[] = [
  'requested',
  'accepted',
  'on_the_way',
  'in_progress',
  'completed',
  'cancelled',
  'declined',
];

const maxUploadSize = 5 * 1024 * 1024;
const allowedImageTypes = ['image/jpeg', 'image/png', 'image/webp'];

function isValidCoordinate(latitude?: number | null, longitude?: number | null) {
  return (
    typeof latitude === 'number' &&
    typeof longitude === 'number' &&
    Number.isFinite(latitude) &&
    Number.isFinite(longitude) &&
    latitude >= -90 &&
    latitude <= 90 &&
    longitude >= -180 &&
    longitude <= 180
  );
}

function requestBrowserLocation(): Promise<Coordinates> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Location is not supported by this browser.'));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const coords = {
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        };
        if (!isValidCoordinate(coords.latitude, coords.longitude)) {
          reject(new Error('Browser returned invalid coordinates.'));
          return;
        }
        resolve(coords);
      },
      () => reject(new Error('Location permission denied or unavailable.')),
      { enableHighAccuracy: true, maximumAge: 60000, timeout: 10000 },
    );
  });
}

function googleMapsDirectionsUrl(origin: Coordinates, destination: Coordinates) {
  return `https://www.google.com/maps/dir/?api=1&origin=${origin.latitude},${origin.longitude}&destination=${destination.latitude},${destination.longitude}`;
}

type Session = {
  accessToken: string;
  refreshToken: string;
  user: User;
};

type ShellProps = {
  session: Session;
  onSession: (session: Session) => void;
  onLogout: () => void;
};

type ScreenProps = ShellProps & {
  notify: (message: string, kind?: 'success' | 'error') => void;
};

function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [loadingSession, setLoadingSession] = useState(true);
  const [notice, setNotice] = useState<{ text: string; kind: 'success' | 'error' } | null>(
    null,
  );

  const clearSession = useCallback(() => {
    localStorage.removeItem(storedAccessKey);
    localStorage.removeItem(storedRefreshKey);
    setSession(null);
  }, []);

  useEffect(() => {
    const accessToken = localStorage.getItem(storedAccessKey);
    const refreshToken = localStorage.getItem(storedRefreshKey);
    if (!accessToken || !refreshToken) {
      setLoadingSession(false);
      return;
    }

    api
      .profile(accessToken)
      .then((user) => setSession({ accessToken, refreshToken, user }))
      .catch(() => clearSession())
      .finally(() => setLoadingSession(false));
  }, [clearSession]);

  const persistSession = useCallback((result: AuthResponse) => {
    localStorage.setItem(storedAccessKey, result.access);
    localStorage.setItem(storedRefreshKey, result.refresh);
    setSession({
      accessToken: result.access,
      refreshToken: result.refresh,
      user: result.user,
    });
  }, []);

  const updateSession = useCallback((next: Session) => {
    setSession(next);
  }, []);

  const logout = useCallback(async () => {
    if (session) {
      await api.logout(session.accessToken, session.refreshToken).catch(() => undefined);
    }
    clearSession();
  }, [clearSession, session]);

  const notify = useCallback((text: string, kind: 'success' | 'error' = 'success') => {
    setNotice({ text, kind });
    window.setTimeout(() => setNotice(null), 3600);
  }, []);

  if (loadingSession) {
    return <div className="center-state">Preparing WorkersBridge...</div>;
  }

  return (
    <BrowserRouter>
      {notice && <div className={`toast ${notice.kind}`}>{notice.text}</div>}
      {!session ? (
        <AuthPage onAuthenticated={persistSession} />
      ) : (
        <AppShell
          session={session}
          onSession={updateSession}
          onLogout={logout}
          notify={notify}
        />
      )}
    </BrowserRouter>
  );
}

function AuthPage({ onAuthenticated }: { onAuthenticated: (result: AuthResponse) => void }) {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [role, setRole] = useState<SignupPayload['role']>('customer');
  const [emailForOtp, setEmailForOtp] = useState('');
  const [otpSent, setOtpSent] = useState(false);
  const [signupCoordinates, setSignupCoordinates] = useState<Coordinates | null>(null);
  const [locationPermissionGranted, setLocationPermissionGranted] = useState(false);
  const [locationMessage, setLocationMessage] = useState(
    'Location helps match jobs and directions. You can continue without it.',
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function captureSignupLocation() {
    setLocationMessage('Requesting browser location...');
    try {
      const coords = await requestBrowserLocation();
      setSignupCoordinates(coords);
      setLocationPermissionGranted(true);
      setLocationMessage('Location captured for location-based services.');
    } catch (err) {
      setSignupCoordinates(null);
      setLocationPermissionGranted(false);
      setLocationMessage(
        err instanceof Error
          ? `${err.message} Location-based jobs and directions may be limited.`
          : 'Location unavailable. Location-based jobs and directions may be limited.',
      );
    }
  }

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setLoading(true);
    setError('');
    try {
      const result = await api.login(
        String(form.get('email')),
        String(form.get('password')),
      );
      onAuthenticated(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed.');
    } finally {
      setLoading(false);
    }
  }

  async function sendOtp(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const email = String(form.get('email'));
    setLoading(true);
    setError('');
    try {
      await api.sendSignupOtp(email);
      setEmailForOtp(email);
      setOtpSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not send OTP.');
    } finally {
      setLoading(false);
    }
  }

  async function signup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setLoading(true);
    setError('');
    try {
      const result = await api.signup({
        username: String(form.get('username')),
        email: emailForOtp,
        password: String(form.get('password')),
        role,
        phone_number: String(form.get('phone_number') || ''),
        location: String(form.get('location') || ''),
        latitude: signupCoordinates?.latitude ?? null,
        longitude: signupCoordinates?.longitude ?? null,
        location_permission_granted: locationPermissionGranted,
        email_otp: String(form.get('email_otp')),
      });
      onAuthenticated(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Signup failed.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-story">
        <Logo />
        <div>
          <h1>
            Reliable help.
            <span> Real people.</span>
            <strong> Right when you need it.</strong>
          </h1>
          <p>
            A focused marketplace for booking skilled local workers, managing jobs,
            and keeping every conversation in one place.
          </p>
        </div>
        <div className="trust-list">
          <TrustItem icon={<ShieldCheck />} title="Verified professionals" text="Profiles, ratings, and portfolios in one view" />
          <TrustItem icon={<Star />} title="Quality you can count on" text="Reviews and completion history guide every booking" />
          <TrustItem icon={<Clock3 />} title="On-time, every time" text="Scheduling, status updates, and chat stay connected" />
        </div>
        <div className="auth-photo">
          <div className="worker-portrait">WB</div>
          <div>
            <strong>Today, 10:30 AM</strong>
            <span>Kitchen sink repair confirmed</span>
          </div>
        </div>
      </section>

      <section className="auth-panel">
        <div className="auth-tabs">
          <button type="button" className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>
            Login
          </button>
          <button
            type="button"
            className={mode === 'signup' ? 'active' : ''}
            onClick={() => setMode('signup')}
          >
            Create account
          </button>
        </div>

        {mode === 'login' ? (
          <form className="form-stack" onSubmit={login}>
            <Field label="Email address" name="email" type="email" icon={<Mail />} required />
            <Field label="Password" name="password" type="password" required />
            <button className="primary-action" disabled={loading}>
              {loading ? 'Signing in...' : 'Login'}
            </button>
          </form>
        ) : (
          <>
            <div className="role-grid" aria-label="Select account role">
              <button type="button" className={role === 'customer' ? 'selected' : ''} onClick={() => setRole('customer')}>
                <UserRound /> Customer
              </button>
              <button type="button" className={role === 'worker' ? 'selected' : ''} onClick={() => setRole('worker')}>
                <Wrench /> Worker
              </button>
            </div>

            {!otpSent ? (
              <form className="form-stack" onSubmit={sendOtp}>
                <div>
                  <h2>Send OTP</h2>
                  <p className="muted">Enter your email and we will send a one-time code.</p>
                </div>
                <Field label="Email address" name="email" type="email" icon={<Mail />} required />
                <button className="primary-action" disabled={loading}>
                  {loading ? 'Sending...' : 'Send OTP'}
                </button>
              </form>
            ) : (
              <form className="form-stack" onSubmit={signup}>
                <div>
                  <h2>Verify email</h2>
                  <p className="muted">Enter the 6-digit code sent to {emailForOtp}.</p>
                </div>
                <Field label="Full name" name="username" required />
                <Field label="Phone number" name="phone_number" />
                <Field label="Location" name="location" />
                <div className="location-capture">
                  <button type="button" className="secondary-action" onClick={captureSignupLocation}>
                    Use current location
                  </button>
                  <p className="muted">{locationMessage}</p>
                </div>
                <Field label="Email OTP" name="email_otp" maxLength={6} required />
                <Field label="Password" name="password" type="password" required />
                <button className="primary-action" disabled={loading}>
                  {loading ? 'Creating...' : 'Continue'}
                </button>
                <button type="button" className="link-button" onClick={() => setOtpSent(false)}>
                  Use a different email
                </button>
              </form>
            )}
          </>
        )}

        {error && <p className="form-error">{error}</p>}
      </section>
    </main>
  );
}

function AppShell({ session, onSession, onLogout, notify }: ScreenProps) {
  const role = session.user.role === 'worker' ? 'worker' : 'customer';
  const title = role === 'worker' ? 'Worker dashboard' : 'Find workers';

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <Logo />
        <nav>
          <SideLink to="/" icon={<Home />} label={role === 'worker' ? 'Dashboard' : 'Home'} />
          <SideLink to="/bookings" icon={<CalendarDays />} label={role === 'worker' ? 'Requests' : 'My bookings'} />
          <SideLink to="/messages" icon={<MessageCircle />} label="Messages" />
          <SideLink to="/profile" icon={<Settings />} label="Profile" />
          <SideLink to="/support" icon={<ShieldCheck />} label="Support" />
        </nav>
        <button className="logout-button" onClick={onLogout}>
          <LogOut /> Log out
        </button>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">{session.user.role}</p>
            <h1>{title}</h1>
          </div>
          <div className="topbar-actions">
            <Link className="icon-badge" to="/messages" aria-label="Open messages"><MessageCircle size={18} /></Link>
            <Link className="avatar-link" to="/profile" aria-label="Open profile"><Avatar user={session.user} /></Link>
            <strong>{session.user.username}</strong>
          </div>
        </header>

        <Routes>
          <Route
            path="/"
            element={
              role === 'worker' ? (
                <WorkerDashboard
                  session={session}
                  onSession={onSession}
                  onLogout={onLogout}
                  notify={notify}
                />
              ) : (
                <CustomerDashboard
                  session={session}
                  onSession={onSession}
                  onLogout={onLogout}
                  notify={notify}
                />
              )
            }
          />
          <Route
            path="/bookings"
            element={<BookingsScreen session={session} onSession={onSession} onLogout={onLogout} notify={notify} />}
          />
          <Route
            path="/messages"
            element={<MessagesScreen session={session} onSession={onSession} onLogout={onLogout} notify={notify} />}
          />
          <Route
            path="/profile"
            element={<ProfileScreen session={session} onSession={onSession} onLogout={onLogout} notify={notify} />}
          />
          <Route
            path="/support"
            element={<SupportScreen session={session} onSession={onSession} onLogout={onLogout} notify={notify} />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}

function CustomerDashboard({ session, notify }: ScreenProps) {
  const [categories, setCategories] = useState<CategorySummary[]>([]);
  const [workers, setWorkers] = useState<WorkerProfile[]>([]);
  const [selectedWorker, setSelectedWorker] = useState<WorkerProfile | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [search, setSearch] = useState('');
  const [availableOnly, setAvailableOnly] = useState(true);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [serviceCoordinates, setServiceCoordinates] = useState<Coordinates | null>(null);
  const [serviceLocationMessage, setServiceLocationMessage] = useState(
    'Use your current GPS location for accurate worker directions.',
  );
  const navigate = useNavigate();

  const loadCustomerBookings = useCallback(() => {
    api.customerBookings(session.accessToken).then((result) => setBookings(result.list)).catch(() => undefined);
  }, [session.accessToken]);

  useEffect(() => {
    api.categories().then((result) => setCategories(result.list)).catch(() => undefined);
    loadCustomerBookings();
  }, [loadCustomerBookings]);

  useEffect(() => {
    api
      .nearbyWorkers({ category: selectedCategory, search, availableOnly })
      .then((result) => {
        setWorkers(result.list);
        setSelectedWorker((current) => current ?? result.list[0] ?? null);
      })
      .catch(() => notify('Could not load workers.', 'error'));
  }, [availableOnly, notify, search, selectedCategory]);

  async function bookService(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedWorker) return;
    const form = new FormData(event.currentTarget);
    const scheduledAt = String(form.get('scheduled_at'));
    try {
      const booking = await api.createBooking(session.accessToken, {
        worker_id: selectedWorker.id,
        service_category: selectedWorker.category,
        description: String(form.get('description')),
        address: String(form.get('address') || session.user.location || ''),
        service_latitude: serviceCoordinates?.latitude ?? null,
        service_longitude: serviceCoordinates?.longitude ?? null,
        location_permission_granted: Boolean(serviceCoordinates),
        scheduled_at: new Date(scheduledAt).toISOString(),
        total_amount: selectedWorker.price,
      });
      setBookings((current) => [booking, ...current]);
      notify('Booking request sent.');
      event.currentTarget.reset();
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Could not create booking.', 'error');
    }
  }

  async function captureServiceLocation() {
    setServiceLocationMessage('Requesting service location...');
    try {
      const coords = await requestBrowserLocation();
      setServiceCoordinates(coords);
      setServiceLocationMessage('Service GPS location captured for this booking.');
    } catch (err) {
      setServiceCoordinates(null);
      setServiceLocationMessage(
        err instanceof Error
          ? `${err.message} You can still book, but directions will be unavailable.`
          : 'Location unavailable. You can still book, but directions will be unavailable.',
      );
    }
  }

  return (
    <div className="dashboard-grid customer-grid">
      <section className="content-area">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Categories</p>
            <h2>Book trusted help nearby</h2>
          </div>
          <label className="switch-label">
            Available now
            <input
              type="checkbox"
              checked={availableOnly}
              onChange={(event) => setAvailableOnly(event.target.checked)}
            />
          </label>
        </div>

        <div className="category-row">
          <button type="button" className={!selectedCategory ? 'chip active' : 'chip'} onClick={() => setSelectedCategory('')}>
            <LayoutDashboard size={18} /> All
          </button>
          {categories.slice(0, 6).map((category) => (
            <button
              type="button"
              key={category.category}
              className={selectedCategory === category.category ? 'chip active' : 'chip'}
              onClick={() => setSelectedCategory(category.category)}
            >
              <Wrench size={18} /> {category.category}
            </button>
          ))}
        </div>

        <div className="searchbar">
          <Search />
          <input
            placeholder="Search by service, worker, or location"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </div>

        <div className="worker-list">
          {workers.map((worker) => (
            <button
              type="button"
              key={worker.id}
              className={selectedWorker?.id === worker.id ? 'worker-row selected' : 'worker-row'}
              onClick={() => setSelectedWorker(worker)}
            >
              <Avatar user={worker.user} size="lg" />
              <div>
                <strong>{worker.user.username}</strong>
                <span>{worker.category}</span>
                <small><Star size={14} /> {worker.rating} ({worker.total_reviews})</small>
              </div>
              <div className="worker-meta">
                <span>{worker.experience_years}+ years</span>
                <strong>{money(worker.price)}</strong>
              </div>
            </button>
          ))}
          {!workers.length && <EmptyState title="No workers found" text="Try a different search or category." />}
        </div>
      </section>

      <aside className="detail-panel">
        {selectedWorker ? (
          <>
            <div className="worker-detail-hero">
              <Avatar user={selectedWorker.user} size="xl" />
              <div>
                <h2>{selectedWorker.user.username}</h2>
                <p>{selectedWorker.category}</p>
                <span><Star size={16} /> {selectedWorker.rating} rating</span>
              </div>
            </div>
            <div className="facts-list">
              <span><ShieldCheck /> {selectedWorker.experience_years}+ years experience</span>
              <span><MapPin /> {selectedWorker.user.location || 'Service area available'}</span>
              <span><CheckCircle2 /> {selectedWorker.is_online ? 'Available now' : 'Currently offline'}</span>
            </div>
            <p className="muted">{selectedWorker.bio || 'Skilled professional ready for everyday tasks and larger home projects.'}</p>
            <form className="form-stack compact" onSubmit={bookService}>
              <h3>Book service</h3>
              <Field label="Schedule" name="scheduled_at" type="datetime-local" required />
              <Field label="Address" name="address" defaultValue={session.user.location ?? ''} required />
              <div className="location-capture">
                <button type="button" className="secondary-action" onClick={captureServiceLocation}>
                  Use current service location
                </button>
                <p className="muted">{serviceLocationMessage}</p>
              </div>
              <label className="field">
                <span>Describe your job</span>
                <textarea name="description" placeholder="What needs to be done?" />
              </label>
              <button className="primary-action">Confirm booking</button>
            </form>
          </>
        ) : (
          <EmptyState title="Select a worker" text="Worker details and booking controls appear here." />
        )}
      </aside>

      <section className="panel-span">
        <PanelHeader title="My bookings" action="View all" onAction={() => navigate('/bookings')} />
        <div className="mini-list">
          {bookings.slice(0, 3).map((booking) => (
            <BookingRow key={booking.id} booking={booking} />
          ))}
          {!bookings.length && <EmptyState title="No bookings yet" text="Choose a worker and schedule your first service." />}
        </div>
      </section>
    </div>
  );
}

function WorkerDashboard({ session, notify }: ScreenProps) {
  const [summary, setSummary] = useState<WorkerDashboardSummary | null>(null);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [jobCategories, setJobCategories] = useState<string[]>([]);

  const loadWorkerData = useCallback(() => {
    api.workerDashboard(session.accessToken).then(setSummary).catch(() => undefined);
    api.workerBookings(session.accessToken).then((result) => setBookings(result.list)).catch(() => undefined);
  }, [session.accessToken]);

  useEffect(() => {
    loadWorkerData();
    api.jobCategories().then((result) => setJobCategories(result.list)).catch(() => undefined);
  }, [loadWorkerData]);

  async function updateAvailability(isOnline: boolean) {
    try {
      const profile = await api.updateAvailability(session.accessToken, isOnline);
      setSummary((current) => current && { ...current, profile });
      notify(isOnline ? 'Availability set to online.' : 'Availability set to offline.');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Could not update availability.', 'error');
    }
  }

  async function updateStatus(bookingId: number, status: BookingStatus) {
    try {
      const updated = await api.updateBookingStatus(session.accessToken, bookingId, status);
      setBookings((current) => current.map((booking) => (booking.id === bookingId ? updated : booking)));
      notify('Booking status updated.');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Could not update status.', 'error');
    }
  }

  async function openDirections(booking: Booking) {
    const destinationLatitude = Number(booking.service_latitude);
    const destinationLongitude = Number(booking.service_longitude);
    if (!isValidCoordinate(destinationLatitude, destinationLongitude)) {
      notify('This booking does not have a saved service GPS location.', 'error');
      return;
    }
    try {
      const origin = await requestBrowserLocation();
      window.open(
        googleMapsDirectionsUrl(origin, {
          latitude: destinationLatitude,
          longitude: destinationLongitude,
        }),
        '_blank',
        'noopener,noreferrer',
      );
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Could not get current location.', 'error');
    }
  }

  async function saveWorkerProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const profile = await api.saveWorkerProfile(session.accessToken, {
        category: String(form.get('category')),
        price: String(form.get('price')),
        experience_years: Number(form.get('experience_years')),
        bio: String(form.get('bio')),
        is_online: Boolean(form.get('is_online')),
      });
      setSummary((current) => current && { ...current, profile });
      notify('Worker profile saved.');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Could not save worker profile.', 'error');
    }
  }

  async function uploadPortfolio(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const images = form
      .getAll('images')
      .filter((value): value is File => value instanceof File && value.size > 0);
    if (!images.length) {
      notify('Choose at least one portfolio image.', 'error');
      return;
    }
    if (images.some((image) => !allowedImageTypes.includes(image.type))) {
      notify('Upload JPG, PNG, or WebP portfolio images only.', 'error');
      return;
    }
    if (images.some((image) => image.size > maxUploadSize)) {
      notify('Each portfolio image must be 5 MB or smaller.', 'error');
      return;
    }
    try {
      await api.uploadWorkImages(session.accessToken, form);
      await loadWorkerData();
      event.currentTarget.reset();
      notify('Portfolio images uploaded.');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Could not upload portfolio images.', 'error');
    }
  }

  async function deletePortfolioImage(imageId: number) {
    try {
      await api.deleteWorkImage(session.accessToken, imageId);
      await loadWorkerData();
      notify('Portfolio image deleted.');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Could not delete portfolio image.', 'error');
    }
  }

  const metrics = summary?.metrics;
  const profile = summary?.profile;

  return (
    <div className="dashboard-grid worker-grid">
      <section className="profile-summary">
        <Avatar user={session.user} size="xl" />
        <div>
          <h2>{session.user.username}</h2>
          <p>{profile?.category || 'Set up your worker profile'}</p>
          <span><MapPin size={16} /> {session.user.location || 'Add service area'}</span>
        </div>
        <label className="switch-label">
          Available now
          <input
            type="checkbox"
            checked={profile?.is_online ?? false}
            onChange={(event) => updateAvailability(event.target.checked)}
            disabled={!profile}
          />
        </label>
      </section>

      <Metric icon={<BriefcaseBusiness />} label="Pending requests" value={metrics?.pending_requests ?? 0} />
      <Metric icon={<Clock3 />} label="Active jobs" value={metrics?.active_jobs ?? 0} />
      <Metric icon={<CheckCircle2 />} label="Completed jobs" value={metrics?.completed_jobs ?? 0} />
      <Metric icon={<DollarSign />} label="Total earnings" value={money(metrics?.total_earnings ?? '0')} />

      <section className="content-area">
        <PanelHeader title="Booking requests" action="Refresh" onAction={loadWorkerData} />
        <div className="booking-table">
          {bookings.slice(0, 6).map((booking) => (
            <article key={booking.id} className="booking-card">
              <div>
                <strong>{booking.service_category}</strong>
                <span>{booking.address}</span>
                <small>{formatDate(booking.scheduled_at)} · {booking.status_display}</small>
              </div>
              <strong>{money(booking.total_amount)}</strong>
              <div className="button-row">
                <button type="button" className="secondary-action" onClick={() => openDirections(booking)}>
                  Get Directions
                </button>
                {booking.status === 'requested' && (
                  <>
                    <button type="button" onClick={() => updateStatus(booking.id, 'accepted')}>Accept</button>
                    <button type="button" className="secondary-action" onClick={() => updateStatus(booking.id, 'declined')}>Decline</button>
                  </>
                )}
                {booking.status === 'accepted' && <button type="button" onClick={() => updateStatus(booking.id, 'on_the_way')}>On the way</button>}
                {['accepted', 'on_the_way'].includes(booking.status) && (
                  <button type="button" className="secondary-action" onClick={() => updateStatus(booking.id, 'in_progress')}>Start</button>
                )}
                {booking.status === 'in_progress' && <button type="button" onClick={() => updateStatus(booking.id, 'completed')}>Complete</button>}
              </div>
            </article>
          ))}
          {!bookings.length && <EmptyState title="No booking requests" text="New customer requests will appear here." />}
        </div>
      </section>

      <aside className="detail-panel">
        <form className="form-stack compact" onSubmit={saveWorkerProfile}>
          <h2>Profile setup</h2>
          <label className="field">
            <span>Category</span>
            <select name="category" defaultValue={profile?.category ?? ''} required>
              <option value="">Choose category</option>
              {jobCategories.map((category) => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </label>
          <Field label="Hourly rate" name="price" type="number" defaultValue={profile?.price ?? ''} required />
          <Field label="Experience years" name="experience_years" type="number" defaultValue={String(profile?.experience_years ?? 1)} required />
          <label className="field">
            <span>Bio</span>
            <textarea name="bio" defaultValue={profile?.bio ?? ''} placeholder="Describe your work and service quality" />
          </label>
          <label className="check-row"><input name="is_online" type="checkbox" defaultChecked={profile?.is_online ?? true} /> Available now</label>
          <button className="primary-action">Save profile</button>
        </form>

        <div className="portfolio-grid">
          <PanelHeader title="Portfolio" />
          <form className="portfolio-upload" onSubmit={uploadPortfolio}>
            <label className="field">
              <span>Upload work photos</span>
              <input name="images" type="file" accept="image/jpeg,image/png,image/webp" multiple disabled={!profile} />
            </label>
            <Field label="Caption" name="caption" placeholder="Optional caption" />
            <button className="secondary-action" disabled={!profile}>
              <UploadCloud size={18} /> Upload
            </button>
          </form>
          {profile?.work_images?.length ? (
            <div className="image-grid">
              {profile.work_images.slice(0, 6).map((image) => (
                <figure key={image.id} className="portfolio-item">
                  <img src={image.image_url ?? ''} alt={image.caption || 'Worker portfolio'} />
                  <button type="button" className="danger-icon" onClick={() => deletePortfolioImage(image.id)} aria-label="Delete portfolio image">
                    <Trash2 size={15} />
                  </button>
                </figure>
              ))}
            </div>
          ) : (
            <div className="upload-placeholder"><ImagePlus /> Portfolio photos appear here after upload.</div>
          )}
        </div>
      </aside>
    </div>
  );
}

function BookingsScreen({ session, notify }: ScreenProps) {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [status, setStatus] = useState<BookingStatus | ''>('');
  const [reviewingId, setReviewingId] = useState<number | null>(null);
  const isWorker = session.user.role === 'worker';

  const loadBookings = useCallback(() => {
    const request = isWorker
      ? api.workerBookings(session.accessToken, status || undefined)
      : api.customerBookings(session.accessToken, status || undefined);
    request.then((result) => setBookings(result.list)).catch(() => notify('Could not load bookings.', 'error'));
  }, [isWorker, notify, session.accessToken, status]);

  useEffect(() => {
    loadBookings();
  }, [loadBookings]);

  async function updateStatus(bookingId: number, nextStatus: BookingStatus) {
    try {
      const updated = await api.updateBookingStatus(session.accessToken, bookingId, nextStatus);
      setBookings((current) => current.map((booking) => (booking.id === bookingId ? updated : booking)));
      notify('Booking status updated.');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Could not update status.', 'error');
    }
  }

  async function openDirections(booking: Booking) {
    const destinationLatitude = Number(booking.service_latitude);
    const destinationLongitude = Number(booking.service_longitude);
    if (!isValidCoordinate(destinationLatitude, destinationLongitude)) {
      notify('This booking does not have a saved service GPS location.', 'error');
      return;
    }
    try {
      const origin = await requestBrowserLocation();
      window.open(
        googleMapsDirectionsUrl(origin, {
          latitude: destinationLatitude,
          longitude: destinationLongitude,
        }),
        '_blank',
        'noopener,noreferrer',
      );
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Could not get current location.', 'error');
    }
  }

  async function submitReview(event: FormEvent<HTMLFormElement>, bookingId: number) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await api.createReview(
        session.accessToken,
        bookingId,
        Number(form.get('rating')),
        String(form.get('feedback') || ''),
      );
      setBookings((current) =>
        current.map((booking) =>
          booking.id === bookingId ? { ...booking, has_review: true } : booking,
        ),
      );
      setReviewingId(null);
      notify('Review submitted.');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Could not submit review.', 'error');
    }
  }

  return (
    <section className="page-panel">
      <PanelHeader title={isWorker ? 'Requests and jobs' : 'My bookings'} action="Refresh" onAction={loadBookings} />
      <div className="category-row">
        <button type="button" className={!status ? 'chip active' : 'chip'} onClick={() => setStatus('')}>All</button>
        {bookingStatuses.map((item) => (
          <button type="button" key={item} className={status === item ? 'chip active' : 'chip'} onClick={() => setStatus(item)}>
            {labelize(item)}
          </button>
        ))}
      </div>
      <div className="mini-list spacious">
        {bookings.map((booking) => (
          <article key={booking.id} className="booking-detail-card">
            <BookingRow booking={booking} />
            <div className="button-row booking-actions">
              {isWorker && (
                <button type="button" className="secondary-action" onClick={() => openDirections(booking)}>
                  Get Directions
                </button>
              )}
              {isWorker && booking.status === 'requested' && (
                <>
                  <button type="button" onClick={() => updateStatus(booking.id, 'accepted')}>Accept</button>
                  <button type="button" className="secondary-action" onClick={() => updateStatus(booking.id, 'declined')}>Decline</button>
                </>
              )}
              {isWorker && booking.status === 'accepted' && (
                <button type="button" onClick={() => updateStatus(booking.id, 'on_the_way')}>On the way</button>
              )}
              {isWorker && ['accepted', 'on_the_way'].includes(booking.status) && (
                <button type="button" className="secondary-action" onClick={() => updateStatus(booking.id, 'in_progress')}>Start</button>
              )}
              {isWorker && booking.status === 'in_progress' && (
                <button type="button" onClick={() => updateStatus(booking.id, 'completed')}>Complete</button>
              )}
              {!isWorker && booking.status === 'completed' && !booking.has_review && (
                <button type="button" onClick={() => setReviewingId(booking.id)}>Review</button>
              )}
            </div>
            {!isWorker && reviewingId === booking.id && (
              <form className="review-form" onSubmit={(event) => submitReview(event, booking.id)}>
                <label className="field">
                  <span>Rating</span>
                  <select name="rating" defaultValue="5">
                    <option value="5">5 stars</option>
                    <option value="4">4 stars</option>
                    <option value="3">3 stars</option>
                    <option value="2">2 stars</option>
                    <option value="1">1 star</option>
                  </select>
                </label>
                <label className="field">
                  <span>Feedback</span>
                  <textarea name="feedback" placeholder="Share your experience" />
                </label>
                <button>Submit review</button>
                <button type="button" className="secondary-action" onClick={() => setReviewingId(null)}>Cancel</button>
              </form>
            )}
          </article>
        ))}
        {!bookings.length && <EmptyState title="No bookings found" text="Bookings matching this filter will appear here." />}
      </div>
    </section>
  );
}

function MessagesScreen({ session, notify }: ScreenProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);

  const loadConversations = useCallback(() => {
    api
      .conversations(session.accessToken)
      .then((result) => {
        setConversations(result.list);
        setSelectedId((current) => current ?? result.list[0]?.id ?? null);
      })
      .catch(() => notify('Could not load conversations.', 'error'));
  }, [notify, session.accessToken]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    if (!selectedId) return;
    api.messages(session.accessToken, selectedId).then((result) => setMessages(result.list)).catch(() => undefined);
  }, [selectedId, session.accessToken]);

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedId) return;
    const form = new FormData(event.currentTarget);
    const text = String(form.get('text'));
    try {
      const message = await api.sendMessage(session.accessToken, selectedId, text);
      setMessages((current) => [...current, message]);
      loadConversations();
      event.currentTarget.reset();
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Could not send message.', 'error');
    }
  }

  return (
    <section className="messages-layout">
      <div className="conversation-list">
        <PanelHeader title="Messages" action="Refresh" onAction={loadConversations} />
        {conversations.map((conversation) => (
          <button
            type="button"
            key={conversation.id}
            className={selectedId === conversation.id ? 'conversation-row selected' : 'conversation-row'}
            onClick={() => setSelectedId(conversation.id)}
          >
            <Avatar user={conversation.booking.customer.id === session.user.id ? conversation.booking.worker.user : conversation.booking.customer} />
            <div>
              <strong>{conversation.other_party_name}</strong>
              <span>{conversation.last_message?.text ?? 'No messages yet'}</span>
            </div>
            {!!conversation.unread_count && <small>{conversation.unread_count}</small>}
          </button>
        ))}
      </div>
      <div className="chat-panel">
        <div className="chat-stream">
          {messages.map((message) => (
            <div key={message.id} className={message.sender.id === session.user.id ? 'bubble mine' : 'bubble'}>
              <span>{message.text}</span>
              <small>{formatDate(message.created_at)}</small>
            </div>
          ))}
          {!messages.length && <EmptyState title="No messages yet" text="Start the conversation from here." />}
        </div>
        <form className="chat-form" onSubmit={sendMessage}>
          <input name="text" placeholder="Write a message" required />
          <button>Send</button>
        </form>
      </div>
    </section>
  );
}

function ProfileScreen({ session, onSession, notify }: ScreenProps) {
  const [photoPreview, setPhotoPreview] = useState(session.user.profile_photo_url ?? '');

  async function updateProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = new FormData();
    payload.set('username', String(form.get('username')));
    payload.set('email', String(form.get('email')));
    payload.set('phone_number', String(form.get('phone_number') || ''));
    payload.set('location', String(form.get('location') || ''));

    const photo = form.get('profile_photo');
    if (photo instanceof File && photo.size > 0) {
      if (!allowedImageTypes.includes(photo.type)) {
        notify('Upload a JPG, PNG, or WebP profile photo.', 'error');
        return;
      }
      if (photo.size > maxUploadSize) {
        notify('Profile photo must be 5 MB or smaller.', 'error');
        return;
      }
      payload.set('profile_photo', photo);
    }

    try {
      const user = await api.updateProfileForm(session.accessToken, payload);
      onSession({ ...session, user });
      setPhotoPreview(user.profile_photo_url ?? '');
      notify('Profile updated.');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Could not update profile.', 'error');
    }
  }

  async function changePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      await api.changePassword(
        session.accessToken,
        String(form.get('old_password')),
        String(form.get('new_password')),
        String(form.get('confirm_password')),
      );
      event.currentTarget.reset();
      notify('Password changed.');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Could not change password.', 'error');
    }
  }

  return (
    <div className="settings-grid">
      <form className="page-panel form-stack" onSubmit={updateProfile}>
        <PanelHeader title="Edit profile" />
        <div className="profile-photo-editor">
          <Avatar user={{ ...session.user, profile_photo_url: photoPreview }} size="xl" />
          <label className="field">
            <span>Profile photo</span>
            <input
              name="profile_photo"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(event) => {
                const file = event.currentTarget.files?.[0];
                if (!file) return;
                if (!allowedImageTypes.includes(file.type)) {
                  notify('Upload a JPG, PNG, or WebP profile photo.', 'error');
                  event.currentTarget.value = '';
                  return;
                }
                if (file.size > maxUploadSize) {
                  notify('Profile photo must be 5 MB or smaller.', 'error');
                  event.currentTarget.value = '';
                  return;
                }
                setPhotoPreview(URL.createObjectURL(file));
              }}
            />
          </label>
        </div>
        <Field label="Full name" name="username" defaultValue={session.user.username} required />
        <Field label="Email" name="email" type="email" defaultValue={session.user.email} required />
        <Field label="Phone" name="phone_number" defaultValue={session.user.phone_number ?? ''} />
        <Field label="Location" name="location" defaultValue={session.user.location ?? ''} />
        <button className="primary-action">Save profile</button>
      </form>

      <form className="page-panel form-stack" onSubmit={changePassword}>
        <PanelHeader title="Change password" />
        <Field label="Old password" name="old_password" type="password" required />
        <Field label="New password" name="new_password" type="password" required />
        <Field label="Confirm password" name="confirm_password" type="password" required />
        <button className="primary-action">Update password</button>
      </form>
    </div>
  );
}

function SupportScreen({ session, notify }: ScreenProps) {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);

  const loadTickets = useCallback(() => {
    api.supportTickets(session.accessToken).then((result) => setTickets(result.list)).catch(() => undefined);
  }, [session.accessToken]);

  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

  async function createTicket(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    try {
      const ticket = await api.createSupportTicket(
        session.accessToken,
        String(form.get('subject')),
        String(form.get('message')),
      );
      setTickets((current) => [ticket, ...current]);
      event.currentTarget.reset();
      notify('Support ticket submitted.');
    } catch (err) {
      notify(err instanceof Error ? err.message : 'Could not submit ticket.', 'error');
    }
  }

  return (
    <div className="settings-grid">
      <form className="page-panel form-stack" onSubmit={createTicket}>
        <PanelHeader title="Help and support" />
        <Field label="Subject" name="subject" required />
        <label className="field">
          <span>Message</span>
          <textarea name="message" placeholder="Tell us what happened" required />
        </label>
        <button className="primary-action">Submit ticket</button>
      </form>
      <section className="page-panel">
        <PanelHeader title="Tickets" action="Refresh" onAction={loadTickets} />
        <div className="mini-list">
          {tickets.map((ticket) => (
            <article key={ticket.id} className="ticket-card">
              <strong>{ticket.subject}</strong>
              <span>{ticket.status_display}</span>
              <p>{ticket.message}</p>
              {ticket.admin_note && <small>Admin note: {ticket.admin_note}</small>}
            </article>
          ))}
          {!tickets.length && <EmptyState title="No tickets" text="Submitted support tickets appear here." />}
        </div>
      </section>
    </div>
  );
}

function SideLink({ to, icon, label }: { to: string; icon: ReactNode; label: string }) {
  return (
    <NavLink to={to} end={to === '/'}>
      {icon}
      {label}
    </NavLink>
  );
}

function Logo() {
  return (
    <div className="logo">
      <span>WB</span>
      <strong>WorkersBridge</strong>
    </div>
  );
}

function TrustItem({ icon, title, text }: { icon: ReactNode; title: string; text: string }) {
  return (
    <article>
      <span>{icon}</span>
      <div>
        <strong>{title}</strong>
        <p>{text}</p>
      </div>
    </article>
  );
}

function Field({
  label,
  icon,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  icon?: ReactNode;
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <div className={icon ? 'input-wrap' : undefined}>
        {icon}
        <input {...props} />
      </div>
    </label>
  );
}

function PanelHeader({
  title,
  action,
  onAction,
}: {
  title: string;
  action?: string;
  onAction?: () => void;
}) {
  return (
    <div className="panel-header">
      <h2>{title}</h2>
      {action && (
        <button type="button" className="link-button" onClick={onAction}>
          {action === 'Refresh' && <RefreshCw size={15} />}
          {action}
        </button>
      )}
    </div>
  );
}

function Metric({ icon, label, value }: { icon: ReactNode; label: string; value: string | number }) {
  return (
    <article className="metric-card">
      <span>{icon}</span>
      <strong>{value}</strong>
      <p>{label}</p>
    </article>
  );
}

function Avatar({ user, size = 'md' }: { user: User; size?: 'md' | 'lg' | 'xl' }) {
  const initials = useMemo(
    () =>
      user.username
        .split(/\s|_/)
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part[0]?.toUpperCase())
        .join('') || 'WB',
    [user.username],
  );

  if (user.profile_photo_url) {
    return <img className={`avatar ${size}`} src={user.profile_photo_url} alt={user.username} />;
  }
  return <span className={`avatar ${size}`}>{initials}</span>;
}

function BookingRow({ booking }: { booking: Booking }) {
  return (
    <article className="booking-row">
      <Avatar user={booking.worker.user} />
      <div>
        <strong>{booking.service_category}</strong>
        <span>{booking.worker.user.username}</span>
      </div>
      <div>
        <strong>{formatDate(booking.scheduled_at)}</strong>
        <span>{booking.address}</span>
      </div>
      <span className={`status ${booking.status}`}>{booking.status_display}</span>
      <strong>{money(booking.total_amount)}</strong>
    </article>
  );
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <div className="empty-state">
      <Sparkles />
      <strong>{title}</strong>
      <p>{text}</p>
    </div>
  );
}

function money(value: string | number) {
  const parsed = Number(value);
  if (Number.isNaN(parsed)) return String(value);
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(parsed);
}

function formatDate(value: string) {
  if (!value) return '';
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value));
}

function labelize(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default App;
