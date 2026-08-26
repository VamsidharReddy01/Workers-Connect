import AsyncStorage from '@react-native-async-storage/async-storage';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import * as Notifications from 'expo-notifications';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Alert,
  Image,
  Linking,
  Pressable,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Switch,
  Text,
  TextInput,
  View,
} from 'react-native';
import { api } from './src/api';
import {
  deregisterPushToken,
  getPendingNotificationTarget,
  registerPushToken,
  resolveNavigationTarget,
  type NavigationTarget,
  type NotificationData,
} from './src/notifications';
import type {
  AppNotification,
  AuthResponse,
  Booking,
  BookingStatus,
  CategorySummary,
  Conversation,
  Coordinates,
  Message,
  SignupPayload,
  SupportTicket,
  User,
  WorkerDashboardSummary,
  WorkerProfile,
} from './src/types';

// ─── Constants ────────────────────────────────────────────────────────────────
const accessKey = 'workersbridge.access';
const refreshKey = 'workersbridge.refresh';
const maxUploadSize = 5 * 1024 * 1024;
const allowedImageTypes = ['image/jpeg', 'image/png', 'image/webp'];

// ─── Types ────────────────────────────────────────────────────────────────────
type Session = {
  accessToken: string;
  refreshToken: string;
  user: User;
};

type Tab = 'home' | 'bookings' | 'messages' | 'profile' | 'support';

type Screen =
  | 'workerBookingDetail'
  | 'customerBookingDetail'
  | 'notifications';

type ScreenProps = {
  session: Session;
  updateSession: (session: Session) => void;
  logout: () => void;
};

type PickedImage = {
  uri: string;
  name: string;
  type: string;
  size?: number;
};

// ─── Utilities ────────────────────────────────────────────────────────────────
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

async function requestDeviceLocation(): Promise<Coordinates> {
  const permission = await Location.requestForegroundPermissionsAsync();
  if (!permission.granted) {
    throw new Error('Location permission was denied. You can continue, but location-based services need access.');
  }
  const servicesEnabled = await Location.hasServicesEnabledAsync();
  if (!servicesEnabled) {
    throw new Error('Location services are turned off. Please enable GPS/location services and try again.');
  }
  const position = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High });
  const coords = { latitude: position.coords.latitude, longitude: position.coords.longitude };
  if (!isValidCoordinate(coords.latitude, coords.longitude)) {
    throw new Error('Your device returned an invalid location.');
  }
  return coords;
}

function googleMapsDirectionsUrl(origin: Coordinates, destination: Coordinates) {
  return `https://www.google.com/maps/dir/?api=1&origin=${origin.latitude},${origin.longitude}&destination=${destination.latitude},${destination.longitude}`;
}

async function openDirectionsForBooking(booking: Booking) {
  if (booking.service_latitude == null || booking.service_longitude == null) {
    Alert.alert('Location missing', 'This booking does not have a saved service location.');
    return;
  }
  const destLat = Number(booking.service_latitude);
  const destLng = Number(booking.service_longitude);
  if (!isValidCoordinate(destLat, destLng)) {
    Alert.alert('Location missing', 'This booking does not have a valid service location.');
    return;
  }
  try {
    const origin = await requestDeviceLocation();
    const url = googleMapsDirectionsUrl(origin, { latitude: destLat, longitude: destLng });
    await Linking.openURL(url);
  } catch (error) {
    showError('Could not open directions', error);
  }
}

function showError(title: string, error: unknown) {
  Alert.alert(title, error instanceof Error ? error.message : 'Try again.');
}

function parseSchedule(value: string) {
  const normalized = value.trim().replace(' ', 'T');
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) throw new Error('Enter schedule as YYYY-MM-DD HH:mm.');
  return date.toISOString();
}

function money(value: string | number) {
  const parsed = Number(value);
  if (Number.isNaN(parsed)) return String(value);
  return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(parsed);
}

function formatDate(value: string) {
  if (!value) return '';
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(new Date(value));
}

function formatTime(value: string) {
  if (!value) return '';
  return new Intl.DateTimeFormat('en-US', { hour: 'numeric', minute: '2-digit' }).format(new Date(value));
}

function timeAgo(value: string) {
  if (!value) return '';
  const diff = Date.now() - new Date(value).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function labelize(value: string) {
  return value.replaceAll('_', ' ').replace(/\b\w/g, (l) => l.toUpperCase());
}

function mimeFromUri(uri: string) {
  const ext = uri.split('.').pop()?.toLowerCase();
  if (ext === 'jpg' || ext === 'jpeg') return 'image/jpeg';
  if (ext === 'webp') return 'image/webp';
  return 'image/png';
}

function extensionFromMime(mime: string) {
  if (mime === 'image/jpeg') return 'jpg';
  if (mime === 'image/webp') return 'webp';
  return 'png';
}

function statusStyle(s: BookingStatus) {
  if (s === 'completed') return styles.statusAmber;
  if (s === 'cancelled' || s === 'declined') return styles.statusDanger;
  return styles.statusPrimary;
}

function notifIcon(type: string) {
  switch (type) {
    case 'JOB_REQUEST_RECEIVED': return '📋';
    case 'JOB_ACCEPTED': return '✅';
    case 'JOB_DECLINED': return '❌';
    case 'WORKER_ON_THE_WAY': return '🚗';
    case 'JOB_STARTED': return '🔧';
    case 'JOB_COMPLETED': return '🎉';
    case 'JOB_CANCELLED': return '🚫';
    case 'NEW_MESSAGE': return '💬';
    default: return '🔔';
  }
}

async function pickImage(): Promise<PickedImage | null> {
  const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
  if (!permission.granted) {
    Alert.alert('Permission needed', 'Allow photo access to upload images.');
    return null;
  }
  const result = await ImagePicker.launchImageLibraryAsync({
    allowsEditing: true,
    mediaTypes: ImagePicker.MediaTypeOptions.Images,
    quality: 0.82,
  });
  if (result.canceled) return null;
  const asset = result.assets[0];
  const type = asset.mimeType || mimeFromUri(asset.uri);
  if (!allowedImageTypes.includes(type)) {
    Alert.alert('Invalid image', 'Upload JPG, PNG, or WebP images only.');
    return null;
  }
  if (asset.fileSize && asset.fileSize > maxUploadSize) {
    Alert.alert('Image too large', 'Images must be 5 MB or smaller.');
    return null;
  }
  return { uri: asset.uri, name: asset.fileName || `upload.${extensionFromMime(type)}`, type, size: asset.fileSize };
}

// ─── App Root ─────────────────────────────────────────────────────────────────
export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [booting, setBooting] = useState(true);

  useEffect(() => {
    async function restore() {
      const [[, accessToken], [, refreshToken]] = await AsyncStorage.multiGet([accessKey, refreshKey]);
      if (!accessToken || !refreshToken) { setBooting(false); return; }
      try {
        const user = await api.profile(accessToken);
        setSession({ accessToken, refreshToken, user });
      } catch {
        try {
          const { access } = await api.refresh(refreshToken);
          const user = await api.profile(access);
          await AsyncStorage.setItem(accessKey, access);
          setSession({ accessToken: access, refreshToken, user });
        } catch { /* keep degraded state */ }
      } finally {
        setBooting(false);
      }
    }
    restore();
  }, []);

  const persistSession = useCallback(async (result: AuthResponse) => {
    await AsyncStorage.multiSet([[accessKey, result.access], [refreshKey, result.refresh]]);
    setSession({ accessToken: result.access, refreshToken: result.refresh, user: result.user });
  }, []);

  const updateSession = useCallback((next: Session) => setSession(next), []);

  const logout = useCallback(async () => {
    if (session) {
      await deregisterPushToken(session.accessToken).catch(() => undefined);
      await api.logout(session.accessToken, session.refreshToken).catch(() => undefined);
    }
    await AsyncStorage.multiRemove([accessKey, refreshKey]);
    setSession(null);
  }, [session]);

  if (booting) {
    return (
      <SafeAreaView style={styles.screen}>
        <StatusBar style="dark" />
        <View style={styles.center}>
          <Text style={styles.mutedStrong}>Preparing WorkersBridge...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!session) return <AuthScreen onAuthenticated={persistSession} />;
  return <MainApp session={session} updateSession={updateSession} logout={logout} />;
}

// ─── Auth Screen ──────────────────────────────────────────────────────────────
function AuthScreen({ onAuthenticated }: { onAuthenticated: (result: AuthResponse) => void }) {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [role, setRole] = useState<SignupPayload['role']>('customer');
  const [otpSent, setOtpSent] = useState(false);
  const [emailForOtp, setEmailForOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [signupCoordinates, setSignupCoordinates] = useState<Coordinates | null>(null);
  const [locationPermissionGranted, setLocationPermissionGranted] = useState(false);
  const [locationSource, setLocationSource] = useState<'gps' | 'manual' | null>(null);
  const [locationMessage, setLocationMessage] = useState('');
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [signupForm, setSignupForm] = useState({
    username: '',
    email: '',
    password: '',
    phone_number: '',
    location: '',
    category: 'Electrician',
    email_otp: '',
  });

  async function login() {
    setLoading(true);
    try {
      const result = await api.login(loginForm.email.trim(), loginForm.password);
      await onAuthenticated(result);
    } catch (error) { showError('Login failed', error); }
    finally { setLoading(false); }
  }

  async function sendOtp() {
    setLoading(true);
    try {
      await api.sendSignupOtp(signupForm.email.trim());
      setEmailForOtp(signupForm.email.trim());
      setOtpSent(true);
      Alert.alert('OTP sent', 'Check your email for the verification code.');
    } catch (error) { showError('Could not send OTP', error); }
    finally { setLoading(false); }
  }

  async function signup() {
    setLoading(true);
    try {
      const result = await api.signup({
        username: signupForm.username.trim(),
        email: emailForOtp,
        password: signupForm.password,
        role,
        category: role === 'worker' ? signupForm.category.trim() || 'General Maintenance' : undefined,
        phone_number: signupForm.phone_number.trim(),
        location: signupForm.location.trim(),
        latitude: signupCoordinates ? parseFloat(signupCoordinates.latitude.toFixed(6)) : null,
        longitude: signupCoordinates ? parseFloat(signupCoordinates.longitude.toFixed(6)) : null,
        location_permission_granted: locationPermissionGranted,
        location_source: locationSource ?? (signupForm.location.trim() ? 'manual' : undefined),
        email_otp: signupForm.email_otp.trim(),
      });
      await onAuthenticated(result);
    } catch (error) { showError('Signup failed', error); }
    finally { setLoading(false); }
  }

  async function captureSignupLocation() {
    setLoading(true);
    setLocationMessage('Getting your current location...');
    try {
      const coords = await requestDeviceLocation();
      setSignupCoordinates(coords);
      setLocationPermissionGranted(true);
      setLocationSource('gps');
      setLocationMessage('Finding your address...');

      // Reverse geocode via backend to get address name
      try {
        const geo = await api.geocode({ latitude: coords.latitude, longitude: coords.longitude });
        if (geo.location_name) {
          setSignupForm((f) => ({ ...f, location: geo.location_name }));
          setLocationMessage('✓ Current location captured');
        } else {
          setLocationMessage('✓ GPS coordinates captured');
        }
      } catch {
        setLocationMessage('✓ GPS coordinates captured');
      }
    } catch (error) {
      setSignupCoordinates(null);
      setLocationPermissionGranted(false);
      setLocationSource(null);
      setLocationMessage(error instanceof Error ? error.message : 'Location was not saved.');
    } finally { setLoading(false); }
  }

  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar style="dark" />
      <ScrollView contentContainerStyle={styles.authContent}>
        <View style={styles.brandBlock}>
          <Logo />
          <Text style={styles.heroTitle}>Reliable help. Real people.</Text>
          <Text style={styles.heroAccent}>Right when you need it.</Text>
          <Text style={styles.heroCopy}>Book skilled local workers, manage requests, upload portfolios, chat, and get support from one polished mobile app.</Text>
        </View>
        <View style={styles.segment}>
          <Pressable style={[styles.segmentButton, mode === 'login' && styles.segmentActive]} onPress={() => setMode('login')}>
            <Text style={[styles.segmentText, mode === 'login' && styles.segmentTextActive]}>Login</Text>
          </Pressable>
          <Pressable style={[styles.segmentButton, mode === 'signup' && styles.segmentActive]} onPress={() => setMode('signup')}>
            <Text style={[styles.segmentText, mode === 'signup' && styles.segmentTextActive]}>Create account</Text>
          </Pressable>
        </View>
        {mode === 'login' ? (
          <View style={styles.card}>
            <Input label="Email address" value={loginForm.email} onChangeText={(email) => setLoginForm((f) => ({ ...f, email }))} keyboardType="email-address" autoCapitalize="none" />
            <Input label="Password" value={loginForm.password} onChangeText={(password) => setLoginForm((f) => ({ ...f, password }))} secureTextEntry />
            <Button title={loading ? 'Signing in...' : 'Login'} onPress={login} disabled={loading} />
          </View>
        ) : (
          <View style={[styles.card, role === 'worker' && styles.workerCardTheme]}>
            <View style={styles.roleRow}>
              <Pill label="Customer" active={role === 'customer'} onPress={() => setRole('customer')} />
              <Pill label="🛠️ Worker (Pro)" active={role === 'worker'} onPress={() => setRole('worker')} />
            </View>

            {role === 'worker' ? (
              <View style={styles.workerCalloutCard}>
                <Text style={styles.workerBadge}>🛠️ PRO WORKER SIGNUP</Text>
                <Text style={styles.workerCalloutTitle}>Wanna Join as Worker?</Text>
                <Text style={styles.workerCalloutSubtitle}>
                  Register your professional profile, set your work area, and start getting hired by local customers.
                </Text>
              </View>
            ) : (
              <View style={styles.customerCalloutCard}>
                <Text style={styles.customerBadge}>👤 CUSTOMER SIGNUP</Text>
                <Text style={styles.sectionTitle}>Create Customer Account</Text>
                <Text style={styles.muted}>Book skilled professionals for home & everyday services.</Text>
                <Pressable style={styles.joinWorkerBanner} onPress={() => setRole('worker')}>
                  <Text style={styles.joinWorkerBannerText}>🛠️ Wanna Join as Worker? Register here →</Text>
                </Pressable>
              </View>
            )}

            {!otpSent ? (
              <>
                <Input label="Email address" value={signupForm.email} onChangeText={(email) => setSignupForm((f) => ({ ...f, email }))} keyboardType="email-address" autoCapitalize="none" />
                <Button title={loading ? 'Sending...' : role === 'worker' ? 'Send Worker OTP' : 'Send OTP'} onPress={sendOtp} disabled={loading} />
              </>
            ) : (
              <>
                <Text style={styles.sectionTitle}>Verify email</Text>
                <Text style={styles.muted}>Code sent to {emailForOtp}</Text>
                <Input label={role === 'worker' ? "Full name / Pro name" : "Full name"} value={signupForm.username} onChangeText={(username) => setSignupForm((f) => ({ ...f, username }))} />
                {role === 'worker' && (
                  <Input
                    label="Primary Trade / Category"
                    value={signupForm.category}
                    onChangeText={(category) => setSignupForm((f) => ({ ...f, category }))}
                    placeholder="e.g. Electrician, Plumber, Carpenter"
                  />
                )}
                <Input label="Phone" value={signupForm.phone_number} onChangeText={(phone_number) => setSignupForm((f) => ({ ...f, phone_number }))} keyboardType="phone-pad" />
                <Input
                  label={role === 'worker' ? "Service base location" : "Location"}
                  value={signupForm.location}
                  onChangeText={(location) => {
                    setSignupForm((f) => ({ ...f, location }));
                    if (locationSource === 'gps') {
                      setSignupCoordinates(null);
                      setLocationSource('manual');
                      setLocationMessage('');
                    }
                  }}
                  placeholder="e.g. Madhapur, Hyderabad"
                />
                <View style={styles.locationBox}>
                  <Text style={styles.itemTitle}>GPS location</Text>
                  <Text style={styles.muted}>Used for location-based services and worker job directions.</Text>
                  <GhostButton title={signupCoordinates ? 'Update current location' : 'Use current location'} onPress={captureSignupLocation} />
                  {!!locationMessage && (
                    <Text style={locationMessage.startsWith('✓') ? styles.successText : styles.muted}>
                      {locationMessage}
                    </Text>
                  )}
                </View>
                <Input label="Email OTP" value={signupForm.email_otp} onChangeText={(email_otp) => setSignupForm((f) => ({ ...f, email_otp }))} keyboardType="number-pad" maxLength={6} />
                <Input label="Password" value={signupForm.password} onChangeText={(password) => setSignupForm((f) => ({ ...f, password }))} secureTextEntry />
                <Button title={loading ? 'Creating...' : role === 'worker' ? 'Join as Worker' : 'Create Customer Account'} onPress={signup} disabled={loading} />
                <GhostButton title="Use a different email" onPress={() => setOtpSent(false)} />
              </>
            )}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
function MainApp({ session, updateSession, logout }: ScreenProps) {
  const [tab, setTab] = useState<Tab>('home');
  const [screen, setScreen] = useState<Screen | null>(null);
  const [detailBookingId, setDetailBookingId] = useState<number | null>(null);
  const [unreadCount, setUnreadCount] = useState(0);
  const notifListenerRef = useRef<Notifications.Subscription | null>(null);
  const notifResponseListenerRef = useRef<Notifications.Subscription | null>(null);

  // ── Register push token after login ──────────────────────────────────────
  useEffect(() => {
    // Slight delay so the tab UI renders first before asking for permission
    const timer = setTimeout(() => {
      registerPushToken(session.accessToken).catch(() => undefined);
    }, 1500);
    return () => clearTimeout(timer);
  }, [session.accessToken]);

  // ── Load unread count ─────────────────────────────────────────────────────
  const loadUnreadCount = useCallback(() => {
    api.getUnreadCount(session.accessToken)
      .then((res) => setUnreadCount(res.count))
      .catch(() => undefined);
  }, [session.accessToken]);

  useEffect(() => {
    loadUnreadCount();
    const interval = setInterval(loadUnreadCount, 30000);
    return () => clearInterval(interval);
  }, [loadUnreadCount]);

  // ── Cold-start: check if app was opened via notification ─────────────────
  useEffect(() => {
    getPendingNotificationTarget(session.user.role as 'customer' | 'worker' | 'admin').then((target) => {
      if (target) applyNavigationTarget(target);
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ── Foreground notification handler ───────────────────────────────────────
  useEffect(() => {
    notifListenerRef.current = Notifications.addNotificationReceivedListener(() => {
      loadUnreadCount();
    });
    // Background/tap notification handler
    notifResponseListenerRef.current = Notifications.addNotificationResponseReceivedListener((response) => {
      const data = response.notification.request.content.data as NotificationData;
      const target = resolveNavigationTarget(data, session.user.role as 'customer' | 'worker' | 'admin');
      if (target) applyNavigationTarget(target);
      loadUnreadCount();
    });
    return () => {
      notifListenerRef.current?.remove();
      notifResponseListenerRef.current?.remove();
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [session.user.role]);

  function applyNavigationTarget(target: NavigationTarget) {
    if (!target) return;
    if (target.screen === 'notifications') {
      setScreen('notifications');
    } else if (target.screen === 'workerBookingDetail' && 'bookingId' in target) {
      setDetailBookingId(target.bookingId);
      setScreen('workerBookingDetail');
    } else if (target.screen === 'customerBookingDetail' && 'bookingId' in target) {
      setDetailBookingId(target.bookingId);
      setScreen('customerBookingDetail');
    } else if (target.screen === 'messages') {
      setTab('messages');
      setScreen(null);
    }
  }

  function openNotifications() {
    setScreen('notifications');
  }

  function openWorkerBookingDetail(bookingId: number) {
    setDetailBookingId(bookingId);
    setScreen('workerBookingDetail');
  }

  function openCustomerBookingDetail(bookingId: number) {
    setDetailBookingId(bookingId);
    setScreen('customerBookingDetail');
  }

  function closeScreen() {
    setScreen(null);
    setDetailBookingId(null);
    loadUnreadCount();
  }

  const title = tab === 'home'
    ? (session.user.role === 'worker' ? 'Worker Dashboard' : 'Find Workers')
    : labelize(tab);

  // ── Render overlay screens ────────────────────────────────────────────────
  if (screen === 'notifications') {
    return (
      <SafeAreaView style={styles.screen}>
        <StatusBar style="dark" />
        <NotificationsScreen session={session} onClose={closeScreen} onNavigate={applyNavigationTarget} />
      </SafeAreaView>
    );
  }

  if (screen === 'workerBookingDetail' && detailBookingId != null) {
    return (
      <SafeAreaView style={styles.screen}>
        <StatusBar style="dark" />
        <WorkerBookingDetailScreen
          session={session}
          bookingId={detailBookingId}
          onBack={closeScreen}
        />
      </SafeAreaView>
    );
  }

  if (screen === 'customerBookingDetail' && detailBookingId != null) {
    return (
      <SafeAreaView style={styles.screen}>
        <StatusBar style="dark" />
        <CustomerBookingDetailScreen
          session={session}
          bookingId={detailBookingId}
          onBack={closeScreen}
        />
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar style="dark" />
      <View style={styles.appHeader}>
        <View>
          <Text style={styles.eyebrow}>{session.user.role}</Text>
          <Text style={styles.title}>{title}</Text>
        </View>
        <View style={styles.headerActions}>
          <Pressable style={styles.iconButton} onPress={openNotifications}>
            <Text style={styles.iconText}>🔔</Text>
            {unreadCount > 0 && (
              <View style={styles.headerBadge}>
                <Text style={styles.headerBadgeText}>{unreadCount > 99 ? '99+' : unreadCount}</Text>
              </View>
            )}
          </Pressable>
          <Pressable style={styles.iconButton} onPress={() => setTab('messages')}>
            <Text style={styles.iconText}>💬</Text>
          </Pressable>
          <Pressable onPress={() => setTab('profile')}>
            <Avatar user={session.user} size={44} />
          </Pressable>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {tab === 'home' && (
          session.user.role === 'worker'
            ? <WorkerHome session={session} updateSession={updateSession} logout={logout} onOpenBookingDetail={openWorkerBookingDetail} />
            : <CustomerHome session={session} updateSession={updateSession} logout={logout} onOpenBookingDetail={openCustomerBookingDetail} />
        )}
        {tab === 'bookings' && (
          <BookingsScreen
            session={session}
            updateSession={updateSession}
            logout={logout}
            onOpenWorkerDetail={openWorkerBookingDetail}
            onOpenCustomerDetail={openCustomerBookingDetail}
          />
        )}
        {tab === 'messages' && <MessagesScreen session={session} updateSession={updateSession} logout={logout} />}
        {tab === 'profile' && <ProfileScreen session={session} updateSession={updateSession} logout={logout} />}
        {tab === 'support' && <SupportScreen session={session} updateSession={updateSession} logout={logout} />}
      </ScrollView>

      <View style={styles.tabbar}>
        <TabButton label="Home" icon="🏠" active={tab === 'home'} onPress={() => setTab('home')} />
        <TabButton label="Bookings" icon="📋" active={tab === 'bookings'} onPress={() => setTab('bookings')} />
        <TabButton label="Messages" icon="💬" active={tab === 'messages'} onPress={() => setTab('messages')} />
        <TabButton label="Profile" icon="👤" active={tab === 'profile'} onPress={() => setTab('profile')} />
        <TabButton label="Support" icon="🎧" active={tab === 'support'} onPress={() => setTab('support')} />
      </View>
    </SafeAreaView>
  );
}

// ─── Worker Booking Detail Screen ─────────────────────────────────────────────
function WorkerBookingDetailScreen({
  session,
  bookingId,
  onBack,
}: { session: Session; bookingId: number; onBack: () => void }) {
  const [booking, setBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setLoading(true);
    api.workerBookings(session.accessToken)
      .then((res) => {
        const found = res.list.find((b) => b.id === bookingId);
        if (found) { setBooking(found); setError(''); }
        else setError('Booking not found.');
      })
      .catch(() => setError('Could not load booking. Please try again.'))
      .finally(() => setLoading(false));
  }, [session.accessToken, bookingId]);

  async function updateStatus(newStatus: BookingStatus) {
    if (!booking) return;
    setActionLoading(true);
    try {
      const updated = await api.updateBookingStatus(session.accessToken, booking.id, newStatus);
      setBooking(updated);
      Alert.alert('Success', `Job status updated to ${updated.status_display}.`);
    } catch (err) { showError('Could not update status', err); }
    finally { setActionLoading(false); }
  }

  async function confirmComplete() {
    Alert.alert(
      'Complete Job?',
      'Are you sure this job has been completed?',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Complete', style: 'default', onPress: () => updateStatus('completed') },
      ],
    );
  }

  async function confirmDecline() {
    Alert.alert(
      'Decline Request?',
      'Are you sure you want to decline this job?',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Decline', style: 'destructive', onPress: () => updateStatus('declined') },
      ],
    );
  }

  if (loading) {
    return (
      <View style={styles.detailContainer}>
        <ScreenHeader title="Job Details" onBack={onBack} />
        <View style={styles.center}><Text style={styles.muted}>Loading...</Text></View>
      </View>
    );
  }

  if (error || !booking) {
    return (
      <View style={styles.detailContainer}>
        <ScreenHeader title="Job Details" onBack={onBack} />
        <View style={styles.center}>
          <Text style={styles.muted}>{error || 'Booking not found.'}</Text>
          <GhostButton title="Go Back" onPress={onBack} />
        </View>
      </View>
    );
  }

  const customer = booking.customer;
  const isTerminal = ['completed', 'cancelled', 'declined'].includes(booking.status);

  return (
    <View style={styles.detailContainer}>
      <ScreenHeader title="Job Details" onBack={onBack} />
      <ScrollView contentContainerStyle={styles.detailContent}>
        {/* Status badge */}
        <View style={styles.statusRow}>
          <Text style={[styles.status, statusStyle(booking.status)]}>{booking.status_display}</Text>
        </View>

        {/* Customer card */}
        <View style={styles.card}>
          <Text style={styles.sectionLabel}>CUSTOMER</Text>
          <View style={styles.personRow}>
            <Avatar user={customer} size={56} />
            <View style={styles.flex}>
              <Text style={styles.itemTitle}>{customer.username}</Text>
              {customer.phone_number ? (
                <Pressable onPress={() => Linking.openURL(`tel:${customer.phone_number}`)}>
                  <Text style={styles.phoneLink}>📞 {customer.phone_number}</Text>
                </Pressable>
              ) : null}
              <Text style={styles.muted}>Customer</Text>
            </View>
          </View>
        </View>

        {/* Service details */}
        <View style={styles.card}>
          <Text style={styles.sectionLabel}>SERVICE</Text>
          <Text style={styles.itemTitle}>{booking.service_category}</Text>
          {booking.description ? (
            <Text style={styles.muted}>{booking.description}</Text>
          ) : null}
        </View>

        {/* Schedule */}
        <View style={styles.card}>
          <Text style={styles.sectionLabel}>SCHEDULE</Text>
          <View style={styles.row}>
            <Text style={styles.detailIcon}>📅</Text>
            <Text style={styles.muted}>{formatDate(booking.scheduled_at)}</Text>
          </View>
        </View>

        {/* Location */}
        <View style={styles.card}>
          <Text style={styles.sectionLabel}>LOCATION</Text>
          <View style={styles.row}>
            <Text style={styles.detailIcon}>📍</Text>
            <Text style={[styles.muted, styles.flex]}>{booking.address || 'No address provided'}</Text>
          </View>
          {booking.service_latitude && booking.service_longitude ? (
            <Text style={styles.coordText}>
              {Number(booking.service_latitude).toFixed(4)}, {Number(booking.service_longitude).toFixed(4)}
            </Text>
          ) : null}
          {!isTerminal && (
            <GhostButton title="Get Directions" onPress={() => openDirectionsForBooking(booking)} />
          )}
        </View>

        {/* Payment */}
        <View style={styles.card}>
          <Text style={styles.sectionLabel}>BUDGET</Text>
          <Text style={styles.priceDisplay}>{money(booking.total_amount)}</Text>
        </View>

        {/* Action buttons based on status */}
        {!isTerminal && (
          <View style={styles.actionCard}>
            {booking.status === 'requested' && (
              <>
                <Button
                  title={actionLoading ? 'Accepting...' : 'Accept Job'}
                  onPress={() => updateStatus('accepted')}
                  disabled={actionLoading}
                />
                <GhostButton
                  title={actionLoading ? '...' : 'Decline'}
                  onPress={confirmDecline}
                />
              </>
            )}
            {booking.status === 'accepted' && (
              <Button
                title={actionLoading ? 'Updating...' : "I'm On The Way"}
                onPress={() => updateStatus('on_the_way')}
                disabled={actionLoading}
              />
            )}
            {booking.status === 'on_the_way' && (
              <Button
                title={actionLoading ? 'Starting...' : 'Start Job'}
                onPress={() => updateStatus('in_progress')}
                disabled={actionLoading}
              />
            )}
            {booking.status === 'in_progress' && (
              <Button
                title={actionLoading ? 'Completing...' : 'Complete Job'}
                onPress={confirmComplete}
                disabled={actionLoading}
              />
            )}
          </View>
        )}

        {booking.status === 'completed' && (
          <View style={[styles.card, styles.successCard]}>
            <Text style={styles.successText}>🎉 Job successfully completed!</Text>
            <Text style={styles.muted}>Completed on {formatDate(booking.updated_at)}</Text>
          </View>
        )}

        {booking.status === 'declined' && (
          <View style={[styles.card, styles.dangerCard]}>
            <Text style={styles.dangerText}>This request was declined.</Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

// ─── Customer Booking Detail Screen ───────────────────────────────────────────
function CustomerBookingDetailScreen({
  session,
  bookingId,
  onBack,
}: { session: Session; bookingId: number; onBack: () => void }) {
  const [booking, setBooking] = useState<Booking | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [reviewForm, setReviewForm] = useState({ rating: '5', feedback: '' });
  const [showReview, setShowReview] = useState(false);

  useEffect(() => {
    setLoading(true);
    api.customerBookings(session.accessToken)
      .then((res) => {
        const found = res.list.find((b) => b.id === bookingId);
        if (found) { setBooking(found); setError(''); }
        else setError('Booking not found.');
      })
      .catch(() => setError('Could not load booking. Please try again.'))
      .finally(() => setLoading(false));
  }, [session.accessToken, bookingId]);

  async function submitReview() {
    if (!booking) return;
    try {
      await api.createReview(session.accessToken, booking.id, Number(reviewForm.rating), reviewForm.feedback);
      setBooking((b) => b ? { ...b, has_review: true } : b);
      setShowReview(false);
      Alert.alert('Review submitted', 'Thank you for your feedback!');
    } catch (err) { showError('Could not submit review', err); }
  }

  const statusMessages: Record<BookingStatus, string> = {
    requested: '⏳ Waiting for worker to accept your request...',
    accepted: '✅ Worker has accepted your request',
    on_the_way: '🚗 Worker is on the way to your location',
    in_progress: '🔧 Worker has started working on your request',
    completed: '🎉 Job has been completed',
    declined: '❌ Worker could not accept this request',
    cancelled: '🚫 This request was cancelled',
  };

  if (loading) {
    return (
      <View style={styles.detailContainer}>
        <ScreenHeader title="My Booking" onBack={onBack} />
        <View style={styles.center}><Text style={styles.muted}>Loading...</Text></View>
      </View>
    );
  }

  if (error || !booking) {
    return (
      <View style={styles.detailContainer}>
        <ScreenHeader title="My Booking" onBack={onBack} />
        <View style={styles.center}>
          <Text style={styles.muted}>{error || 'Booking not found.'}</Text>
          <GhostButton title="Go Back" onPress={onBack} />
        </View>
      </View>
    );
  }

  const worker = booking.worker;

  return (
    <View style={styles.detailContainer}>
      <ScreenHeader title="My Booking" onBack={onBack} />
      <ScrollView contentContainerStyle={styles.detailContent}>
        {/* Status */}
        <View style={styles.statusRow}>
          <Text style={[styles.status, statusStyle(booking.status)]}>{booking.status_display}</Text>
        </View>
        <View style={[styles.card, styles.statusMessageCard]}>
          <Text style={styles.statusMessage}>{statusMessages[booking.status]}</Text>
        </View>

        {/* Worker card */}
        <View style={styles.card}>
          <Text style={styles.sectionLabel}>WORKER</Text>
          <View style={styles.personRow}>
            <Avatar user={worker.user} size={56} />
            <View style={styles.flex}>
              <Text style={styles.itemTitle}>{worker.user.username}</Text>
              <Text style={styles.muted}>{worker.category}</Text>
              <Text style={styles.rating}>⭐ {worker.rating} ({worker.total_reviews} reviews)</Text>
            </View>
          </View>
        </View>

        {/* Service */}
        <View style={styles.card}>
          <Text style={styles.sectionLabel}>SERVICE</Text>
          <Text style={styles.itemTitle}>{booking.service_category}</Text>
          {booking.description ? <Text style={styles.muted}>{booking.description}</Text> : null}
        </View>

        {/* Schedule */}
        <View style={styles.card}>
          <Text style={styles.sectionLabel}>SCHEDULE</Text>
          <View style={styles.row}>
            <Text style={styles.detailIcon}>📅</Text>
            <Text style={styles.muted}>{formatDate(booking.scheduled_at)}</Text>
          </View>
        </View>

        {/* Location */}
        <View style={styles.card}>
          <Text style={styles.sectionLabel}>LOCATION</Text>
          <View style={styles.row}>
            <Text style={styles.detailIcon}>📍</Text>
            <Text style={[styles.muted, styles.flex]}>{booking.address || 'No address'}</Text>
          </View>
        </View>

        {/* Payment */}
        <View style={styles.card}>
          <Text style={styles.sectionLabel}>BUDGET</Text>
          <Text style={styles.priceDisplay}>{money(booking.total_amount)}</Text>
        </View>

        {/* Review */}
        {booking.status === 'completed' && !booking.has_review && (
          <View style={styles.card}>
            <Text style={styles.sectionLabel}>REVIEW</Text>
            {!showReview ? (
              <GhostButton title="Leave a Review" onPress={() => setShowReview(true)} />
            ) : (
              <>
                <Input label="Rating (1–5)" value={reviewForm.rating} onChangeText={(rating) => setReviewForm((f) => ({ ...f, rating }))} keyboardType="number-pad" />
                <Input label="Feedback" value={reviewForm.feedback} onChangeText={(feedback) => setReviewForm((f) => ({ ...f, feedback }))} multiline />
                <Button title="Submit Review" onPress={submitReview} />
                <GhostButton title="Cancel" onPress={() => setShowReview(false)} />
              </>
            )}
          </View>
        )}
        {booking.status === 'completed' && booking.has_review && (
          <View style={[styles.card, styles.successCard]}>
            <Text style={styles.successText}>✅ Review submitted. Thank you!</Text>
          </View>
        )}
      </ScrollView>
    </View>
  );
}

// ─── Notifications Screen ─────────────────────────────────────────────────────
function NotificationsScreen({
  session,
  onClose,
  onNavigate,
}: {
  session: Session;
  onClose: () => void;
  onNavigate: (target: NavigationTarget) => void;
}) {
  const [notifications, setNotifications] = useState<AppNotification[]>([]);
  const [filter, setFilter] = useState<'all' | 'unread'>('all');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const loadNotifications = useCallback(() => {
    setLoading(true);
    api.getNotifications(session.accessToken, filter === 'unread')
      .then((res) => { setNotifications(res.list); setError(''); })
      .catch(() => setError('Could not load notifications.'))
      .finally(() => setLoading(false));
  }, [session.accessToken, filter]);

  useEffect(() => { loadNotifications(); }, [loadNotifications]);

  async function markAllRead() {
    try {
      await api.markAllNotificationsRead(session.accessToken);
      setNotifications((list) => list.map((n) => ({ ...n, is_read: true })));
    } catch { /* silent */ }
  }

  async function handleTap(notif: AppNotification) {
    // Mark as read
    if (!notif.is_read) {
      api.markNotificationRead(session.accessToken, notif.id).catch(() => undefined);
      setNotifications((list) => list.map((n) => n.id === notif.id ? { ...n, is_read: true } : n));
    }
    // Navigate
    const target = resolveNavigationTarget(
      notif.data as NotificationData,
      session.user.role as 'customer' | 'worker' | 'admin',
    );
    if (target && target.screen !== 'notifications') {
      onClose();
      setTimeout(() => onNavigate(target), 100);
    }
  }

  const unread = notifications.filter((n) => !n.is_read).length;

  return (
    <View style={styles.detailContainer}>
      <View style={styles.notifHeader}>
        <Pressable style={styles.backButton} onPress={onClose}>
          <Text style={styles.backButtonText}>← Back</Text>
        </Pressable>
        <Text style={styles.sectionTitle}>Notifications</Text>
        {unread > 0 && (
          <Pressable style={styles.markAllBtn} onPress={markAllRead}>
            <Text style={styles.markAllText}>Mark all read</Text>
          </Pressable>
        )}
      </View>

      <View style={styles.filterRow}>
        <Pill label={`All (${notifications.length})`} active={filter === 'all'} onPress={() => setFilter('all')} />
        <Pill label={`Unread (${unread})`} active={filter === 'unread'} onPress={() => setFilter('unread')} />
      </View>

      <ScrollView contentContainerStyle={styles.detailContent}>
        {loading && <Text style={[styles.muted, { textAlign: 'center' }]}>Loading...</Text>}
        {!loading && error && (
          <View style={styles.center}>
            <Text style={styles.muted}>{error}</Text>
            <GhostButton title="Retry" onPress={loadNotifications} />
          </View>
        )}
        {!loading && !error && notifications.length === 0 && (
          <EmptyState title="No notifications" text="You're all caught up! Notifications will appear here." />
        )}
        {notifications.map((notif) => (
          <Pressable
            key={notif.id}
            style={[styles.notifItem, !notif.is_read && styles.notifUnread]}
            onPress={() => handleTap(notif)}
          >
            <Text style={styles.notifIcon}>{notifIcon(notif.notification_type)}</Text>
            <View style={styles.flex}>
              <Text style={[styles.notifTitle, !notif.is_read && styles.notifTitleUnread]}>
                {notif.title}
              </Text>
              <Text style={styles.notifMessage} numberOfLines={2}>{notif.message}</Text>
              <Text style={styles.notifTime}>{timeAgo(notif.created_at)}</Text>
            </View>
            {!notif.is_read && <View style={styles.unreadDot} />}
          </Pressable>
        ))}
      </ScrollView>
    </View>
  );
}

// ─── Customer Home ────────────────────────────────────────────────────────────
function CustomerHome({
  session,
  onOpenBookingDetail,
}: ScreenProps & { onOpenBookingDetail: (id: number) => void }) {
  const [categories, setCategories] = useState<CategorySummary[]>([]);
  const [workers, setWorkers] = useState<WorkerProfile[]>([]);
  const [selectedWorker, setSelectedWorker] = useState<WorkerProfile | null>(null);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [availableOnly, setAvailableOnly] = useState(true);
  const [serviceCoordinates, setServiceCoordinates] = useState<Coordinates | null>(
    session.user.latitude && session.user.longitude
      ? { latitude: Number(session.user.latitude), longitude: Number(session.user.longitude) }
      : null,
  );
  const [serviceLocationSource, setServiceLocationSource] = useState<'saved' | 'gps' | 'manual' | null>(
    session.user.location || (session.user.latitude && session.user.longitude) ? 'saved' : null,
  );
  const [serviceLocationMessage, setServiceLocationMessage] = useState(
    session.user.location ? '✓ Using your saved location' : '',
  );
  const [bookingForm, setBookingForm] = useState({
    scheduled_at: '',
    address: session.user.location ?? '',
    description: '',
  });

  const loadBookings = useCallback(() => {
    api.customerBookings(session.accessToken).then((r) => setBookings(r.list)).catch(() => undefined);
  }, [session.accessToken]);

  useEffect(() => {
    api.categories().then((r) => setCategories(r.list)).catch(() => undefined);
    loadBookings();
  }, [loadBookings]);

  useEffect(() => {
    const lat = session.user.latitude ? Number(session.user.latitude) : null;
    const lng = session.user.longitude ? Number(session.user.longitude) : null;
    api.nearbyWorkers({ category, search, availableOnly, lat, lng }, session.accessToken)
      .then((r) => { setWorkers(r.list); setSelectedWorker((c) => c ?? r.list[0] ?? null); })
      .catch((e) => showError('Could not load workers', e));
  }, [availableOnly, category, search, session.accessToken, session.user.latitude, session.user.longitude]);

  async function bookService() {
    if (!selectedWorker) return;
    try {
      const scheduledAt = parseSchedule(bookingForm.scheduled_at);
      const finalAddress = bookingForm.address.trim() || session.user.location || '';
      const booking = await api.createBooking(session.accessToken, {
        worker_id: selectedWorker.id,
        service_category: selectedWorker.category,
        description: bookingForm.description,
        address: finalAddress,
        service_latitude: serviceCoordinates ? parseFloat(serviceCoordinates.latitude.toFixed(6)) : null,
        service_longitude: serviceCoordinates ? parseFloat(serviceCoordinates.longitude.toFixed(6)) : null,
        location_permission_granted: Boolean(serviceCoordinates),
        service_location_source: serviceLocationSource ?? (finalAddress ? 'manual' : undefined),
        scheduled_at: scheduledAt,
        total_amount: selectedWorker.price,
      });
      setBookings((c) => [booking, ...c]);
      setBookingForm({ scheduled_at: '', address: session.user.location ?? '', description: '' });
      setServiceCoordinates(
        session.user.latitude && session.user.longitude
          ? { latitude: Number(session.user.latitude), longitude: Number(session.user.longitude) }
          : null,
      );
      setServiceLocationSource(
        session.user.location || (session.user.latitude && session.user.longitude) ? 'saved' : null,
      );
      setServiceLocationMessage(
        session.user.location ? '✓ Using your saved location' : '',
      );
      Alert.alert('Booking sent', 'Your booking request has been submitted. You will be notified when the worker accepts.');
    } catch (error) { showError('Could not create booking', error); }
  }

  async function captureServiceLocation() {
    setServiceLocationMessage('Getting your current location...');
    try {
      const coords = await requestDeviceLocation();
      setServiceCoordinates(coords);
      setServiceLocationSource('gps');
      setServiceLocationMessage('Finding your address...');

      try {
        const geo = await api.geocode({ latitude: coords.latitude, longitude: coords.longitude });
        if (geo.location_name) {
          setBookingForm((f) => ({ ...f, address: geo.location_name }));
          setServiceLocationMessage('✓ Current service location captured');
        } else {
          setServiceLocationMessage('✓ Current service location captured');
        }
      } catch {
        setServiceLocationMessage('✓ Current service location captured');
      }
    } catch (error) {
      setServiceLocationMessage(error instanceof Error ? error.message : 'Service location was not saved.');
    }
  }

  return (
    <>
      <View style={styles.card}>
        <View style={styles.row}>
          <View>
            <Text style={styles.eyebrow}>Marketplace</Text>
            <Text style={styles.sectionTitle}>Book trusted help nearby</Text>
          </View>
          <Switch value={availableOnly} onValueChange={setAvailableOnly} trackColor={{ false: palette.line, true: palette.primarySoft }} thumbColor={availableOnly ? palette.primary : '#F4F4F5'} />
        </View>
        <Input label="Search" value={search} onChangeText={setSearch} placeholder="Service, worker, or location" />
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRow}>
          <Pill label="All" active={!category} onPress={() => setCategory('')} />
          {categories.slice(0, 8).map((item) => (
            <Pill key={item.category} label={item.category} active={category === item.category} onPress={() => setCategory(item.category)} />
          ))}
        </ScrollView>
      </View>

      {workers.map((worker) => (
        <Pressable key={worker.id} style={[styles.workerCard, selectedWorker?.id === worker.id && styles.selectedCard]} onPress={() => setSelectedWorker(worker)}>
          <Avatar user={worker.user} size={58} />
          <View style={styles.flex}>
            <Text style={styles.itemTitle}>{worker.user.username}</Text>
            <Text style={styles.muted}>{worker.category}</Text>
            {(worker.location_name || worker.user.location) ? (
              <Text style={styles.muted}>
                📍 {worker.location_name || worker.user.location}
                {worker.distance_km != null ? ` • ${worker.distance_km} km` : ''}
              </Text>
            ) : worker.distance_km != null ? (
              <Text style={styles.muted}>📏 {worker.distance_km} km away</Text>
            ) : null}
            <Text style={styles.rating}>⭐ {worker.rating} ({worker.total_reviews})</Text>
          </View>
          <View style={styles.rightMeta}>
            <Text style={styles.price}>{money(worker.price)}</Text>
            <Text style={styles.online}>{worker.is_online ? '● Available' : '○ Offline'}</Text>
          </View>
        </Pressable>
      ))}

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Book service</Text>
        {selectedWorker ? (
          <>
            <Text style={styles.itemTitle}>{selectedWorker.user.username} — {selectedWorker.category}</Text>
            {(selectedWorker.location_name || selectedWorker.user.location) && (
              <Text style={styles.muted}>
                📍 {selectedWorker.location_name || selectedWorker.user.location}
                {selectedWorker.distance_km != null ? ` • ${selectedWorker.distance_km} km away` : ''}
              </Text>
            )}
            <Input label="Schedule" value={bookingForm.scheduled_at} onChangeText={(v) => setBookingForm((f) => ({ ...f, scheduled_at: v }))} placeholder="2026-08-08 18:30" />
            <Input
              label="Address"
              value={bookingForm.address}
              onChangeText={(v) => {
                setBookingForm((f) => ({ ...f, address: v }));
                setServiceCoordinates(null);
                setServiceLocationSource('manual');
                setServiceLocationMessage(v.trim() ? '✓ Address manually entered' : '');
              }}
              placeholder="e.g. Madhapur, Hyderabad"
            />
            <View style={styles.locationBox}>
              <Text style={styles.itemTitle}>Service location</Text>
              <Text style={styles.muted}>Save the exact job location for worker navigation.</Text>
              <GhostButton title={serviceCoordinates ? 'Update service location' : 'Use current service location'} onPress={captureServiceLocation} />
              {!!serviceLocationMessage && (
                <Text style={serviceLocationMessage.startsWith('✓') ? styles.successText : styles.muted}>
                  {serviceLocationMessage}
                </Text>
              )}
            </View>
            <Input label="Describe your job" value={bookingForm.description} onChangeText={(v) => setBookingForm((f) => ({ ...f, description: v }))} multiline />
            <Button title="Confirm booking" onPress={bookService} />
          </>
        ) : (
          <EmptyState title="No worker selected" text="Choose a worker to create a booking." />
        )}
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>My recent bookings</Text>
        {bookings.slice(0, 3).map((booking) => (
          <Pressable key={booking.id} onPress={() => onOpenBookingDetail(booking.id)}>
            <CustomerBookingCard booking={booking} />
          </Pressable>
        ))}
        {!bookings.length && <EmptyState title="No bookings yet" text="Your recent bookings appear here." />}
      </View>
    </>
  );
}

// ─── Worker Home ──────────────────────────────────────────────────────────────
function WorkerHome({
  session,
  onOpenBookingDetail,
}: ScreenProps & { onOpenBookingDetail: (id: number) => void }) {
  const [summary, setSummary] = useState<WorkerDashboardSummary | null>(null);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [jobCategories, setJobCategories] = useState<string[]>([]);
  const [profileForm, setProfileForm] = useState({ category: '', price: '', experience_years: '1', bio: '', is_online: true });

  const profile = summary?.profile;

  const loadWorker = useCallback(() => {
    api.workerDashboard(session.accessToken)
      .then((r) => {
        setSummary(r);
        setProfileForm({ category: r.profile.category, price: r.profile.price, experience_years: String(r.profile.experience_years), bio: r.profile.bio, is_online: r.profile.is_online });
      }).catch(() => undefined);
    api.workerBookings(session.accessToken).then((r) => setBookings(r.list)).catch(() => undefined);
  }, [session.accessToken]);

  useEffect(() => {
    loadWorker();
    api.jobCategories().then((r) => setJobCategories(r.list)).catch(() => undefined);
  }, [loadWorker]);

  async function saveProfile() {
    try {
      const saved = await api.saveWorkerProfile(session.accessToken, { category: profileForm.category, price: profileForm.price, experience_years: Number(profileForm.experience_years), bio: profileForm.bio, is_online: profileForm.is_online });
      setSummary((c) => c && { ...c, profile: saved });
      Alert.alert('Saved', 'Worker profile updated.');
    } catch (error) { showError('Could not save worker profile', error); }
  }

  async function updateAvailability(value: boolean) {
    try {
      const saved = await api.updateAvailability(session.accessToken, value);
      setSummary((c) => c && { ...c, profile: saved });
      setProfileForm((f) => ({ ...f, is_online: saved.is_online }));
    } catch (error) { showError('Could not update availability', error); }
  }

  async function uploadPortfolio() {
    if (!profile) { Alert.alert('Create profile first', 'Save your worker profile before uploading portfolio images.'); return; }
    const image = await pickImage();
    if (!image) return;
    const formData = new FormData();
    formData.append('images', image as unknown as Blob);
    formData.append('caption', 'Portfolio work');
    try { await api.uploadWorkImages(session.accessToken, formData); loadWorker(); Alert.alert('Uploaded', 'Portfolio image uploaded.'); }
    catch (error) { showError('Could not upload portfolio image', error); }
  }

  async function deletePortfolioImage(imageId: number) {
    try { await api.deleteWorkImage(session.accessToken, imageId); loadWorker(); }
    catch (error) { showError('Could not delete image', error); }
  }

  return (
    <>
      <View style={styles.card}>
        <View style={styles.row}>
          <View style={styles.flex}>
            <Text style={styles.sectionTitle}>{session.user.username}</Text>
            <Text style={styles.muted}>{profile?.category || 'Set up your worker profile'}</Text>
          </View>
          <Switch value={profileForm.is_online} onValueChange={updateAvailability} trackColor={{ false: palette.line, true: palette.primarySoft }} thumbColor={profileForm.is_online ? palette.primary : '#F4F4F5'} />
        </View>
      </View>

      <View style={styles.metricsGrid}>
        <Metric label="Pending" value={summary?.metrics.pending_requests ?? 0} />
        <Metric label="Active" value={summary?.metrics.active_jobs ?? 0} />
        <Metric label="Done" value={summary?.metrics.completed_jobs ?? 0} />
        <Metric label="Earnings" value={money(summary?.metrics.total_earnings ?? '0')} />
      </View>

      <View style={styles.card}>
        <View style={styles.row}>
          <Text style={styles.sectionTitle}>Booking Requests</Text>
          <GhostButton title="Refresh" onPress={loadWorker} />
        </View>
        {bookings.slice(0, 5).map((booking) => (
          <Pressable key={booking.id} onPress={() => onOpenBookingDetail(booking.id)}>
            <WorkerBookingCard booking={booking} />
          </Pressable>
        ))}
        {!bookings.length && <EmptyState title="No requests" text="Customer requests appear here." />}
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Profile Setup</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRow}>
          {jobCategories.map((item) => (
            <Pill key={item} label={item} active={profileForm.category === item} onPress={() => setProfileForm((f) => ({ ...f, category: item }))} />
          ))}
        </ScrollView>
        <Input label="Category" value={profileForm.category} onChangeText={(v) => setProfileForm((f) => ({ ...f, category: v }))} />
        <Input label="Hourly rate" value={profileForm.price} onChangeText={(v) => setProfileForm((f) => ({ ...f, price: v }))} keyboardType="decimal-pad" />
        <Input label="Experience years" value={profileForm.experience_years} onChangeText={(v) => setProfileForm((f) => ({ ...f, experience_years: v }))} keyboardType="number-pad" />
        <Input label="Bio" value={profileForm.bio} onChangeText={(v) => setProfileForm((f) => ({ ...f, bio: v }))} multiline />
        <Button title="Save profile" onPress={saveProfile} />
      </View>

      <View style={styles.card}>
        <View style={styles.row}>
          <Text style={styles.sectionTitle}>Portfolio</Text>
          <SmallButton title="Upload" onPress={uploadPortfolio} />
        </View>
        <View style={styles.imageGrid}>
          {profile?.work_images.map((image) => (
            <View key={image.id} style={styles.portfolioItem}>
              {image.image_url ? <Image source={{ uri: image.image_url }} style={styles.portfolioImage} /> : null}
              <Pressable style={styles.deleteButton} onPress={() => deletePortfolioImage(image.id)}>
                <Text style={styles.deleteText}>×</Text>
              </Pressable>
            </View>
          ))}
        </View>
        {!profile?.work_images.length && <EmptyState title="No photos" text="Upload work photos after creating your profile." />}
      </View>
    </>
  );
}

// ─── Bookings Screen ──────────────────────────────────────────────────────────
function BookingsScreen({
  session,
  onOpenWorkerDetail,
  onOpenCustomerDetail,
}: ScreenProps & { onOpenWorkerDetail: (id: number) => void; onOpenCustomerDetail: (id: number) => void }) {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [status, setStatus] = useState<BookingStatus | ''>('');
  const isWorker = session.user.role === 'worker';

  const loadBookings = useCallback(() => {
    const req = isWorker
      ? api.workerBookings(session.accessToken, status || undefined)
      : api.customerBookings(session.accessToken, status || undefined);
    req.then((r) => setBookings(r.list)).catch((e) => showError('Could not load bookings', e));
  }, [isWorker, session.accessToken, status]);

  useEffect(() => { loadBookings(); }, [loadBookings]);

  return (
    <View style={styles.card}>
      <View style={styles.row}>
        <Text style={styles.sectionTitle}>{isWorker ? 'Requests & Jobs' : 'My Bookings'}</Text>
        <GhostButton title="Refresh" onPress={loadBookings} />
      </View>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRow}>
        <Pill label="All" active={!status} onPress={() => setStatus('')} />
        {(['requested', 'accepted', 'on_the_way', 'in_progress', 'completed', 'cancelled', 'declined'] as BookingStatus[]).map((item) => (
          <Pill key={item} label={labelize(item)} active={status === item} onPress={() => setStatus(item)} />
        ))}
      </ScrollView>
      {bookings.map((booking) => (
        <Pressable
          key={booking.id}
          onPress={() => isWorker ? onOpenWorkerDetail(booking.id) : onOpenCustomerDetail(booking.id)}
        >
          {isWorker ? <WorkerBookingCard booking={booking} /> : <CustomerBookingCard booking={booking} />}
        </Pressable>
      ))}
      {!bookings.length && <EmptyState title="No bookings" text="Bookings matching this filter appear here." />}
    </View>
  );
}

// ─── Messages Screen ──────────────────────────────────────────────────────────
function MessagesScreen({ session }: ScreenProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState('');

  const loadConversations = useCallback(() => {
    api.conversations(session.accessToken)
      .then((r) => { setConversations(r.list); setSelectedConversation((c) => c ? r.list.find((conv) => conv.id === c.id) ?? null : null); })
      .catch((e) => showError('Could not load conversations', e));
  }, [session.accessToken]);

  useEffect(() => { loadConversations(); }, [loadConversations]);

  useEffect(() => {
    if (!selectedConversation) { setMessages([]); return; }
    api.messages(session.accessToken, selectedConversation.id)
      .then((r) => setMessages(r.list)).catch(() => undefined);
  }, [selectedConversation, session.accessToken]);

  async function sendMessage() {
    if (!selectedConversation || !text.trim()) return;
    try {
      const message = await api.sendMessage(session.accessToken, selectedConversation.id, text.trim());
      setMessages((c) => [...c, message]);
      setText('');
      loadConversations();
    } catch (error) { showError('Could not send message', error); }
  }

  if (selectedConversation) {
    return (
      <View style={styles.chatPage}>
        <View style={styles.chatHeader}>
          <Pressable style={styles.backButton} onPress={() => { setSelectedConversation(null); setText(''); }}>
            <Text style={styles.backButtonText}>← Back</Text>
          </Pressable>
          <View style={styles.flex}>
            <Text style={styles.sectionTitle}>{selectedConversation.other_party_name}</Text>
            <Text style={styles.muted} numberOfLines={1}>{selectedConversation.booking.service_category} — {selectedConversation.booking.status_display}</Text>
          </View>
        </View>
        <View style={styles.chatBody}>
          {messages.map((message) => (
            <View key={message.id} style={[styles.messageRow, message.sender.id === session.user.id && styles.myMessageRow]}>
              <View style={[styles.bubble, message.sender.id === session.user.id && styles.myBubble]}>
                <Text style={message.sender.id === session.user.id ? styles.myBubbleText : styles.bubbleText}>{message.text}</Text>
                <Text style={message.sender.id === session.user.id ? styles.myBubbleTime : styles.bubbleTime}>{formatDate(message.created_at)}</Text>
              </View>
            </View>
          ))}
          {!messages.length && <EmptyState title="No messages yet" text="Start the conversation from here." />}
        </View>
        <View style={styles.composer}>
          <TextInput onChangeText={setText} placeholder="Write a message" placeholderTextColor={palette.muted} style={styles.composerInput} value={text} />
          <Pressable style={styles.sendButton} onPress={sendMessage}>
            <Text style={styles.sendButtonText}>Send</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.card}>
      <View style={styles.row}>
        <Text style={styles.sectionTitle}>Messages</Text>
        <GhostButton title="Refresh" onPress={loadConversations} />
      </View>
      {conversations.map((conversation) => (
        <Pressable key={conversation.id} style={styles.conversationRow} onPress={() => setSelectedConversation(conversation)}>
          <View style={styles.conversationAvatar}>
            <Text style={styles.conversationAvatarText}>{conversation.other_party_name.slice(0, 1).toUpperCase()}</Text>
          </View>
          <View style={styles.flex}>
            <Text style={styles.itemTitle}>{conversation.other_party_name}</Text>
            <Text style={styles.muted} numberOfLines={1}>{conversation.last_message?.text ?? 'No messages yet'}</Text>
            <Text style={styles.conversationMeta} numberOfLines={1}>{conversation.booking.service_category} — {conversation.booking.status_display}</Text>
          </View>
          {!!conversation.unread_count && <Text style={styles.badge}>{conversation.unread_count}</Text>}
        </Pressable>
      ))}
      {!conversations.length && <EmptyState title="No conversations" text="Chats are created after booking." />}
    </View>
  );
}

// ─── Profile Screen ───────────────────────────────────────────────────────────
function ProfileScreen({ session, updateSession, logout }: ScreenProps) {
  const [profileForm, setProfileForm] = useState({ username: session.user.username, email: session.user.email, phone_number: session.user.phone_number ?? '', location: session.user.location ?? '' });
  const [passwordForm, setPasswordForm] = useState({ old_password: '', new_password: '', confirm_password: '' });
  const [photo, setPhoto] = useState<PickedImage | null>(null);

  async function chooseProfilePhoto() { const image = await pickImage(); if (image) setPhoto(image); }

  async function saveProfile() {
    const formData = new FormData();
    formData.append('username', profileForm.username);
    formData.append('email', profileForm.email);
    formData.append('phone_number', profileForm.phone_number);
    formData.append('location', profileForm.location);
    if (photo) formData.append('profile_photo', photo as unknown as Blob);
    try { const user = await api.updateProfileForm(session.accessToken, formData); updateSession({ ...session, user }); setPhoto(null); Alert.alert('Saved', 'Profile updated.'); }
    catch (error) { showError('Could not update profile', error); }
  }

  async function changePassword() {
    try { await api.changePassword(session.accessToken, passwordForm.old_password, passwordForm.new_password, passwordForm.confirm_password); setPasswordForm({ old_password: '', new_password: '', confirm_password: '' }); Alert.alert('Saved', 'Password changed.'); }
    catch (error) { showError('Could not change password', error); }
  }

  return (
    <>
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Edit Profile</Text>
        <View style={styles.profilePhotoRow}>
          <Avatar user={{ ...session.user, profile_photo_url: photo?.uri ?? session.user.profile_photo_url }} size={76} />
          <GhostButton title="Choose photo" onPress={chooseProfilePhoto} />
        </View>
        <Input label="Full name" value={profileForm.username} onChangeText={(v) => setProfileForm((f) => ({ ...f, username: v }))} />
        <Input label="Email" value={profileForm.email} onChangeText={(v) => setProfileForm((f) => ({ ...f, email: v }))} keyboardType="email-address" autoCapitalize="none" />
        <Input label="Phone" value={profileForm.phone_number} onChangeText={(v) => setProfileForm((f) => ({ ...f, phone_number: v }))} keyboardType="phone-pad" />
        <Input label="Location" value={profileForm.location} onChangeText={(v) => setProfileForm((f) => ({ ...f, location: v }))} />
        <Button title="Save profile" onPress={saveProfile} />
      </View>
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Change Password</Text>
        <Input label="Old password" value={passwordForm.old_password} onChangeText={(v) => setPasswordForm((f) => ({ ...f, old_password: v }))} secureTextEntry />
        <Input label="New password" value={passwordForm.new_password} onChangeText={(v) => setPasswordForm((f) => ({ ...f, new_password: v }))} secureTextEntry />
        <Input label="Confirm password" value={passwordForm.confirm_password} onChangeText={(v) => setPasswordForm((f) => ({ ...f, confirm_password: v }))} secureTextEntry />
        <Button title="Update password" onPress={changePassword} />
      </View>
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Session</Text>
        <GhostButton title="Log out" onPress={logout} />
      </View>
    </>
  );
}

// ─── Support Screen ───────────────────────────────────────────────────────────
function SupportScreen({ session }: ScreenProps) {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [ticketForm, setTicketForm] = useState({ subject: '', message: '' });

  const loadTickets = useCallback(() => {
    api.supportTickets(session.accessToken).then((r) => setTickets(r.list)).catch(() => undefined);
  }, [session.accessToken]);

  useEffect(() => { loadTickets(); }, [loadTickets]);

  async function submitTicket() {
    try {
      const ticket = await api.createSupportTicket(session.accessToken, ticketForm.subject, ticketForm.message);
      setTickets((c) => [ticket, ...c]);
      setTicketForm({ subject: '', message: '' });
      Alert.alert('Submitted', 'Support ticket submitted.');
    } catch (error) { showError('Could not submit ticket', error); }
  }

  return (
    <>
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Help and Support</Text>
        <Input label="Subject" value={ticketForm.subject} onChangeText={(v) => setTicketForm((f) => ({ ...f, subject: v }))} />
        <Input label="Message" value={ticketForm.message} onChangeText={(v) => setTicketForm((f) => ({ ...f, message: v }))} multiline />
        <Button title="Submit ticket" onPress={submitTicket} />
      </View>
      <View style={styles.card}>
        <View style={styles.row}>
          <Text style={styles.sectionTitle}>Tickets</Text>
          <GhostButton title="Refresh" onPress={loadTickets} />
        </View>
        {tickets.map((ticket) => (
          <View key={ticket.id} style={styles.ticket}>
            <Text style={styles.itemTitle}>{ticket.subject}</Text>
            <Text style={styles.online}>{ticket.status_display}</Text>
            <Text style={styles.muted}>{ticket.message}</Text>
            {!!ticket.admin_note && <Text style={styles.note}>Admin note: {ticket.admin_note}</Text>}
          </View>
        ))}
        {!tickets.length && <EmptyState title="No tickets" text="Submitted support tickets appear here." />}
      </View>
    </>
  );
}

// ─── Reusable Card Components ─────────────────────────────────────────────────

/** Worker's view of a booking request — rich info card, tappable */
function WorkerBookingCard({ booking }: { booking: Booking }) {
  return (
    <View style={styles.richBookingCard}>
      {/* Customer info row */}
      <View style={styles.personRow}>
        <Avatar user={booking.customer} size={44} />
        <View style={styles.flex}>
          <Text style={styles.itemTitle}>{booking.customer.username}</Text>
          <Text style={styles.muted}>Customer</Text>
        </View>
        <Text style={[styles.status, statusStyle(booking.status)]}>{booking.status_display}</Text>
      </View>
      {/* Service info */}
      <View style={styles.richBookingBody}>
        <Text style={styles.richCategory}>{booking.service_category}</Text>
        {booking.description ? (
          <Text style={styles.muted} numberOfLines={2}>{booking.description}</Text>
        ) : null}
        <View style={styles.richMeta}>
          <Text style={styles.richMetaItem}>📅 {formatDate(booking.scheduled_at)}</Text>
          <Text style={styles.richMetaItem}>📍 {booking.address || 'No address'}</Text>
          <Text style={styles.richMetaItem}>💰 {money(booking.total_amount)}</Text>
        </View>
      </View>
      <Text style={styles.tapHint}>Tap to view details →</Text>
    </View>
  );
}

/** Customer's view of a booking — shows worker info + status */
function CustomerBookingCard({ booking }: { booking: Booking }) {
  return (
    <View style={styles.richBookingCard}>
      <View style={styles.personRow}>
        <Avatar user={booking.worker.user} size={44} />
        <View style={styles.flex}>
          <Text style={styles.itemTitle}>{booking.worker.user.username}</Text>
          <Text style={styles.muted}>{booking.worker.category}</Text>
        </View>
        <Text style={[styles.status, statusStyle(booking.status)]}>{booking.status_display}</Text>
      </View>
      <View style={styles.richBookingBody}>
        <Text style={styles.richCategory}>{booking.service_category}</Text>
        {booking.description ? <Text style={styles.muted} numberOfLines={2}>{booking.description}</Text> : null}
        <View style={styles.richMeta}>
          <Text style={styles.richMetaItem}>📅 {formatDate(booking.scheduled_at)}</Text>
          <Text style={styles.richMetaItem}>📍 {booking.address || 'No address'}</Text>
          <Text style={styles.richMetaItem}>💰 {money(booking.total_amount)}</Text>
        </View>
      </View>
      <Text style={styles.tapHint}>Tap to view details →</Text>
    </View>
  );
}

// ─── Shared UI Components ─────────────────────────────────────────────────────

function ScreenHeader({ title, onBack }: { title: string; onBack: () => void }) {
  return (
    <View style={styles.screenHeader}>
      <Pressable style={styles.backButton} onPress={onBack}>
        <Text style={styles.backButtonText}>← Back</Text>
      </Pressable>
      <Text style={styles.screenHeaderTitle}>{title}</Text>
    </View>
  );
}

function Input(props: { label: string; value: string; onChangeText: (v: string) => void; placeholder?: string; secureTextEntry?: boolean; keyboardType?: 'default' | 'email-address' | 'number-pad' | 'phone-pad' | 'decimal-pad'; autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters'; multiline?: boolean; maxLength?: number; }) {
  return (
    <View style={styles.inputGroup}>
      <Text style={styles.inputLabel}>{props.label}</Text>
      <TextInput autoCapitalize={props.autoCapitalize} keyboardType={props.keyboardType} maxLength={props.maxLength} multiline={props.multiline} onChangeText={props.onChangeText} placeholder={props.placeholder} placeholderTextColor={palette.muted} secureTextEntry={props.secureTextEntry} style={[styles.input, props.multiline && styles.multiline]} textAlignVertical={props.multiline ? 'top' : 'center'} value={props.value} />
    </View>
  );
}

function Button({ title, onPress, disabled }: { title: string; onPress: () => void; disabled?: boolean }) {
  return (
    <Pressable style={[styles.button, disabled && styles.disabled]} onPress={onPress} disabled={disabled}>
      <Text style={styles.buttonText}>{title}</Text>
    </Pressable>
  );
}

function SmallButton({ title, onPress, variant }: { title: string; onPress: () => void; variant?: 'ghost' }) {
  return (
    <Pressable style={[styles.smallButton, variant === 'ghost' && styles.smallGhost]} onPress={onPress}>
      <Text style={[styles.smallButtonText, variant === 'ghost' && styles.smallGhostText]}>{title}</Text>
    </Pressable>
  );
}

function GhostButton({ title, onPress }: { title: string; onPress: () => void }) {
  return (
    <Pressable style={styles.ghostButton} onPress={onPress}>
      <Text style={styles.ghostText}>{title}</Text>
    </Pressable>
  );
}

function Pill({ label, active, onPress }: { label: string; active: boolean; onPress: () => void }) {
  return (
    <Pressable style={[styles.pill, active && styles.pillActive]} onPress={onPress}>
      <Text style={[styles.pillText, active && styles.pillTextActive]}>{label}</Text>
    </Pressable>
  );
}

function TabButton({ label, icon, active, onPress }: { label: string; icon: string; active: boolean; onPress: () => void }) {
  return (
    <Pressable style={styles.tabButton} onPress={onPress}>
      <Text style={[styles.tabIcon, active && styles.tabActive]}>{icon}</Text>
      <Text style={[styles.tabText, active && styles.tabActive]} numberOfLines={1}>{label}</Text>
    </Pressable>
  );
}

function Logo() {
  return (
    <View style={styles.logo}>
      <View style={styles.logoMark}><Text style={styles.logoMarkText}>WB</Text></View>
      <Text style={styles.logoText}>WorkersBridge</Text>
    </View>
  );
}

function Avatar({ user, size }: { user: User; size: number }) {
  const initials = useMemo(() =>
    user.username.split(/\s|_/).filter(Boolean).slice(0, 2).map((p) => p[0]?.toUpperCase()).join('') || 'WB',
    [user.username]);

  if (user.profile_photo_url) {
    return <Image source={{ uri: user.profile_photo_url }} style={[styles.avatar, { height: size, width: size, borderRadius: size / 2 }]} />;
  }
  return (
    <View style={[styles.avatar, styles.avatarFallback, { height: size, width: size, borderRadius: size / 2 }]}>
      <Text style={[styles.avatarText, { fontSize: size * 0.36 }]}>{initials}</Text>
    </View>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <View style={styles.metric}>
      <Text style={styles.metricValue}>{value}</Text>
      <Text style={styles.metricLabel}>{label}</Text>
    </View>
  );
}

function EmptyState({ title, text }: { title: string; text: string }) {
  return (
    <View style={styles.empty}>
      <Text style={styles.emptyTitle}>{title}</Text>
      <Text style={styles.muted}>{text}</Text>
    </View>
  );
}

// ─── Design System ────────────────────────────────────────────────────────────
const palette = {
  bg: '#F6F8F5',
  surface: '#FFFFFF',
  surfaceSoft: '#EEF7F2',
  line: '#DCE6E1',
  text: '#111827',
  muted: '#60706A',
  primary: '#007F68',
  primaryStrong: '#00624F',
  primarySoft: '#DFF5EE',
  amber: '#F5A400',
  danger: '#DC3D45',
  success: '#00A86B',
};

const styles = StyleSheet.create({
  screen: { backgroundColor: palette.bg, flex: 1 },
  center: { alignItems: 'center', flex: 1, justifyContent: 'center', gap: 12, padding: 20 },
  authContent: { gap: 18, padding: 20 },
  content: { gap: 14, padding: 16, paddingBottom: 92 },
  detailContainer: { flex: 1 },
  detailContent: { gap: 14, padding: 16, paddingBottom: 40 },

  // Brand
  brandBlock: { backgroundColor: '#FBF7EF', borderColor: palette.line, borderRadius: 12, borderWidth: 1, gap: 10, padding: 18 },
  logo: { alignItems: 'center', flexDirection: 'row', gap: 10 },
  logoMark: { alignItems: 'center', backgroundColor: palette.primary, borderRadius: 10, height: 38, justifyContent: 'center', width: 38 },
  logoMarkText: { color: '#FFFFFF', fontSize: 12, fontWeight: '900' },
  logoText: { color: palette.text, fontSize: 20, fontWeight: '900' },
  heroTitle: { color: palette.text, fontSize: 31, fontWeight: '900', lineHeight: 35, marginTop: 8 },
  heroAccent: { color: palette.primaryStrong, fontSize: 29, fontWeight: '900' },
  heroCopy: { color: '#33443F', fontSize: 15, lineHeight: 22 },

  // Segment
  segment: { backgroundColor: palette.surface, borderColor: palette.line, borderRadius: 10, borderWidth: 1, flexDirection: 'row', padding: 4 },
  segmentButton: { alignItems: 'center', borderRadius: 8, flex: 1, padding: 12 },
  segmentActive: { backgroundColor: palette.primarySoft },
  segmentText: { color: palette.muted, fontWeight: '900' },
  segmentTextActive: { color: palette.primaryStrong },

  // Card
  card: { backgroundColor: palette.surface, borderColor: palette.line, borderRadius: 12, borderWidth: 1, gap: 12, padding: 14 },

  // App header
  appHeader: { alignItems: 'center', backgroundColor: palette.surface, borderBottomColor: palette.line, borderBottomWidth: 1, flexDirection: 'row', justifyContent: 'space-between', padding: 16 },
  headerActions: { alignItems: 'center', flexDirection: 'row', gap: 10 },
  iconButton: { alignItems: 'center', backgroundColor: palette.primarySoft, borderRadius: 10, height: 42, justifyContent: 'center', width: 42, position: 'relative' },
  iconText: { fontSize: 18 },
  headerBadge: { position: 'absolute', top: -4, right: -4, backgroundColor: palette.danger, borderRadius: 999, minWidth: 18, height: 18, alignItems: 'center', justifyContent: 'center', paddingHorizontal: 4 },
  headerBadgeText: { color: '#FFFFFF', fontSize: 10, fontWeight: '900' },
  eyebrow: { color: palette.primary, fontSize: 11, fontWeight: '900', letterSpacing: 1, textTransform: 'uppercase' },
  title: { color: palette.text, fontSize: 22, fontWeight: '900' },
  sectionTitle: { color: palette.text, fontSize: 19, fontWeight: '900' },
  sectionLabel: { color: palette.primary, fontSize: 11, fontWeight: '900', letterSpacing: 1, textTransform: 'uppercase' },
  itemTitle: { color: palette.text, fontSize: 15, fontWeight: '900' },
  muted: { color: palette.muted, fontSize: 13, lineHeight: 19 },
  mutedStrong: { color: palette.muted, fontWeight: '900' },

  // Screen header (for detail screens)
  screenHeader: { alignItems: 'center', backgroundColor: palette.surface, borderBottomColor: palette.line, borderBottomWidth: 1, flexDirection: 'row', gap: 12, padding: 14 },
  screenHeaderTitle: { color: palette.text, flex: 1, fontSize: 18, fontWeight: '900' },

  // Input
  inputGroup: { gap: 6 },
  inputLabel: { color: palette.text, fontSize: 13, fontWeight: '900' },
  input: { backgroundColor: palette.surface, borderColor: palette.line, borderRadius: 10, borderWidth: 1, color: palette.text, paddingHorizontal: 13, paddingVertical: 12 },
  multiline: { minHeight: 92 },

  // Buttons
  button: { alignItems: 'center', backgroundColor: palette.primary, borderRadius: 10, padding: 14 },
  disabled: { opacity: 0.62 },
  buttonText: { color: '#FFFFFF', fontWeight: '900', fontSize: 15 },
  ghostButton: { alignItems: 'center', backgroundColor: palette.primarySoft, borderRadius: 10, paddingHorizontal: 13, paddingVertical: 10 },
  ghostText: { color: palette.primaryStrong, fontWeight: '900' },
  smallButton: { alignItems: 'center', backgroundColor: palette.primary, borderRadius: 8, paddingHorizontal: 12, paddingVertical: 9 },
  smallButtonText: { color: '#FFFFFF', fontSize: 12, fontWeight: '900' },
  smallGhost: { backgroundColor: palette.surfaceSoft },
  smallGhostText: { color: palette.primaryStrong },

  // Pills & chips
  roleRow: { flexDirection: 'row', gap: 10 },
  chipRow: { gap: 9 },
  pill: { backgroundColor: palette.surface, borderColor: palette.line, borderRadius: 20, borderWidth: 1, paddingHorizontal: 14, paddingVertical: 10 },
  pillActive: { backgroundColor: palette.primarySoft, borderColor: palette.primary },
  pillText: { color: palette.text, fontWeight: '900', fontSize: 13 },
  pillTextActive: { color: palette.primaryStrong },

  // Layout helpers
  row: { alignItems: 'center', flexDirection: 'row', gap: 12, justifyContent: 'space-between' },
  flex: { flex: 1 },
  personRow: { alignItems: 'center', flexDirection: 'row', gap: 12 },
  statusRow: { alignItems: 'center', flexDirection: 'row' },

  // Worker card
  workerCard: { alignItems: 'center', backgroundColor: palette.surface, borderColor: palette.line, borderRadius: 12, borderWidth: 1, flexDirection: 'row', gap: 12, padding: 12 },
  selectedCard: { backgroundColor: '#F4FFFB', borderColor: palette.primary },
  rating: { color: palette.amber, fontSize: 12, fontWeight: '900', marginTop: 4 },
  rightMeta: { alignItems: 'flex-end' },
  price: { color: palette.text, fontSize: 16, fontWeight: '900' },
  online: { color: palette.primaryStrong, fontSize: 12, fontWeight: '900' },

  // Rich booking cards
  richBookingCard: { backgroundColor: palette.surface, borderColor: palette.line, borderRadius: 12, borderWidth: 1, gap: 10, padding: 14 },
  richBookingBody: { gap: 6 },
  richCategory: { color: palette.text, fontSize: 16, fontWeight: '900' },
  richMeta: { gap: 4, marginTop: 4 },
  richMetaItem: { color: palette.muted, fontSize: 13 },
  tapHint: { color: palette.primary, fontSize: 12, fontWeight: '800', textAlign: 'right' },

  // Detail screen specifics
  priceDisplay: { color: palette.text, fontSize: 28, fontWeight: '900' },
  detailIcon: { fontSize: 16 },
  coordText: { color: palette.muted, fontSize: 11, fontFamily: 'monospace' },
  phoneLink: { color: palette.primary, fontWeight: '900', fontSize: 14 },
  actionCard: { backgroundColor: palette.surface, borderColor: palette.primary, borderRadius: 12, borderWidth: 1, gap: 10, padding: 14 },
  successCard: { backgroundColor: '#F0FFF8', borderColor: palette.success },
  successText: { color: palette.success, fontWeight: '900', fontSize: 15 },
  dangerCard: { backgroundColor: '#FFF1F2', borderColor: palette.danger },
  dangerText: { color: palette.danger, fontWeight: '900', fontSize: 15 },
  statusMessageCard: { backgroundColor: palette.surfaceSoft },
  statusMessage: { color: palette.text, fontSize: 15, fontWeight: '600' },

  // Metrics
  metricsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  metric: { backgroundColor: palette.surface, borderColor: palette.line, borderRadius: 12, borderWidth: 1, flexBasis: '47%', flexGrow: 1, padding: 14 },
  metricValue: { color: palette.text, fontSize: 22, fontWeight: '900' },
  metricLabel: { color: palette.muted, fontSize: 12, marginTop: 4 },

  // Status badges
  status: { borderRadius: 999, fontSize: 11, fontWeight: '900', overflow: 'hidden', paddingHorizontal: 9, paddingVertical: 5, textTransform: 'uppercase' },
  statusPrimary: { backgroundColor: palette.primarySoft, color: palette.primaryStrong },
  statusAmber: { backgroundColor: '#FFF3CF', color: '#915D00' },
  statusDanger: { backgroundColor: '#FFF1F2', color: palette.danger },

  // Portfolio
  imageGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  portfolioItem: { position: 'relative' },
  portfolioImage: { backgroundColor: palette.surfaceSoft, borderRadius: 10, height: 96, width: 96 },
  deleteButton: { alignItems: 'center', backgroundColor: 'rgba(17,24,39,0.82)', borderRadius: 6, height: 28, justifyContent: 'center', position: 'absolute', right: 4, top: 4, width: 28 },
  deleteText: { color: '#FFFFFF', fontSize: 20, fontWeight: '900' },

  // Notifications
  notifHeader: { alignItems: 'center', backgroundColor: palette.surface, borderBottomColor: palette.line, borderBottomWidth: 1, flexDirection: 'row', gap: 10, padding: 14 },
  filterRow: { flexDirection: 'row', gap: 10, padding: 12 },
  notifItem: { alignItems: 'flex-start', backgroundColor: palette.surface, borderColor: palette.line, borderRadius: 12, borderWidth: 1, flexDirection: 'row', gap: 12, marginHorizontal: 16, marginBottom: 10, padding: 14 },
  notifUnread: { backgroundColor: '#F0FFF8', borderColor: palette.primary },
  notifIcon: { fontSize: 22, marginTop: 2 },
  notifTitle: { color: palette.text, fontSize: 14, fontWeight: '700' },
  notifTitleUnread: { fontWeight: '900' },
  notifMessage: { color: palette.muted, fontSize: 13, lineHeight: 18, marginTop: 2 },
  notifTime: { color: palette.muted, fontSize: 11, marginTop: 4 },
  unreadDot: { backgroundColor: palette.primary, borderRadius: 999, height: 8, marginTop: 6, width: 8 },
  markAllBtn: { backgroundColor: palette.primarySoft, borderRadius: 8, paddingHorizontal: 10, paddingVertical: 6 },
  markAllText: { color: palette.primaryStrong, fontSize: 12, fontWeight: '900' },

  // Chat
  chatPage: { gap: 12 },
  chatHeader: { alignItems: 'center', backgroundColor: palette.surface, borderColor: palette.line, borderRadius: 12, borderWidth: 1, flexDirection: 'row', gap: 12, padding: 12 },
  backButton: { alignItems: 'center', backgroundColor: palette.primarySoft, borderRadius: 8, paddingHorizontal: 13, paddingVertical: 10 },
  backButtonText: { color: palette.primaryStrong, fontWeight: '900' },
  chatBody: { backgroundColor: palette.surface, borderColor: palette.line, borderRadius: 12, borderWidth: 1, gap: 10, minHeight: 420, padding: 12 },
  messageRow: { alignItems: 'flex-start', width: '100%' },
  myMessageRow: { alignItems: 'flex-end' },
  bubble: { backgroundColor: palette.surfaceSoft, borderRadius: 10, maxWidth: '86%', padding: 11 },
  myBubble: { backgroundColor: palette.primary },
  bubbleText: { color: palette.text },
  myBubbleText: { color: '#FFFFFF' },
  bubbleTime: { color: palette.muted, fontSize: 10, marginTop: 5 },
  myBubbleTime: { color: '#DFF5EE', fontSize: 10, marginTop: 5 },
  composer: { alignItems: 'center', backgroundColor: palette.surface, borderColor: palette.line, borderRadius: 12, borderWidth: 1, flexDirection: 'row', gap: 10, padding: 10 },
  composerInput: { backgroundColor: palette.surfaceSoft, borderRadius: 10, color: palette.text, flex: 1, paddingHorizontal: 12, paddingVertical: 10 },
  sendButton: { backgroundColor: palette.primary, borderRadius: 10, paddingHorizontal: 14, paddingVertical: 11 },
  sendButtonText: { color: '#FFFFFF', fontWeight: '900' },

  // Conversations
  conversationRow: { alignItems: 'center', borderColor: palette.line, borderRadius: 12, borderWidth: 1, flexDirection: 'row', gap: 5, padding: 11 },
  conversationAvatar: { alignItems: 'center', backgroundColor: palette.primarySoft, borderRadius: 22, height: 44, justifyContent: 'center', marginRight: 8, width: 44 },
  conversationAvatarText: { color: palette.primaryStrong, fontWeight: '900' },
  conversationMeta: { color: palette.primaryStrong, fontSize: 11, fontWeight: '800', marginTop: 3 },
  badge: { alignSelf: 'center', backgroundColor: palette.primary, borderRadius: 999, color: '#FFFFFF', fontSize: 11, fontWeight: '900', paddingHorizontal: 8, paddingVertical: 3, overflow: 'hidden' },

  // Profile
  profilePhotoRow: { alignItems: 'center', backgroundColor: palette.surfaceSoft, borderRadius: 10, flexDirection: 'row', gap: 14, padding: 12 },

  // Support
  ticket: { borderColor: palette.line, borderRadius: 10, borderWidth: 1, gap: 6, padding: 12 },
  note: { backgroundColor: palette.surfaceSoft, borderRadius: 8, color: palette.primaryStrong, fontSize: 12, fontWeight: '800', padding: 8 },

  // Empty / utility
  empty: { alignItems: 'center', borderColor: palette.line, borderRadius: 12, borderStyle: 'dashed', borderWidth: 1, gap: 6, padding: 18 },
  emptyTitle: { color: palette.text, fontWeight: '900' },
  locationBox: { backgroundColor: palette.surfaceSoft, borderColor: palette.line, borderRadius: 10, borderWidth: 1, gap: 8, padding: 12 },
  reviewBox: { backgroundColor: palette.surfaceSoft, borderRadius: 10, gap: 10, padding: 10 },

  // Avatar
  avatar: { borderRadius: 22 },
  avatarFallback: { alignItems: 'center', backgroundColor: palette.primarySoft, borderColor: palette.line, borderWidth: 1, justifyContent: 'center' },
  avatarText: { color: palette.primaryStrong, fontWeight: '900' },

  // Tab bar
  tabbar: { backgroundColor: palette.surface, borderTopColor: palette.line, borderTopWidth: 1, bottom: 0, flexDirection: 'row', left: 0, paddingBottom: 8, paddingTop: 8, position: 'absolute', right: 0 },
  tabButton: { alignItems: 'center', flex: 1, gap: 2 },
  tabIcon: { fontSize: 18 },
  tabText: { color: palette.muted, fontSize: 10, fontWeight: '900' },
  tabActive: { color: palette.primaryStrong },

  // Worker & Customer Signup
  workerCardTheme: { borderColor: palette.primary, backgroundColor: '#F9FDFB' },
  workerCalloutCard: { backgroundColor: '#F0FDF4', borderColor: '#86EFAC', borderRadius: 10, borderWidth: 1, padding: 12, gap: 4 },
  workerBadge: { alignSelf: 'flex-start', backgroundColor: '#059669', borderRadius: 4, color: '#FFFFFF', fontSize: 10, fontWeight: '900', paddingHorizontal: 7, paddingVertical: 3, overflow: 'hidden' },
  workerCalloutTitle: { color: '#166534', fontSize: 17, fontWeight: '900', marginTop: 3 },
  workerCalloutSubtitle: { color: '#15803D', fontSize: 12, lineHeight: 17 },
  customerCalloutCard: { backgroundColor: palette.surfaceSoft, borderColor: palette.line, borderRadius: 10, borderWidth: 1, padding: 12, gap: 4 },
  customerBadge: { alignSelf: 'flex-start', backgroundColor: palette.surface, borderColor: palette.line, borderWidth: 1, borderRadius: 4, color: palette.muted, fontSize: 10, fontWeight: '900', paddingHorizontal: 7, paddingVertical: 3, overflow: 'hidden' },
  joinWorkerBanner: { alignItems: 'center', backgroundColor: '#ECFDF5', borderColor: '#10B981', borderRadius: 8, borderStyle: 'dashed', borderWidth: 1, marginTop: 6, paddingHorizontal: 10, paddingVertical: 9 },
  joinWorkerBannerText: { color: '#047857', fontSize: 12, fontWeight: '800' },
});
