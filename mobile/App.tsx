import AsyncStorage from '@react-native-async-storage/async-storage';
import * as ImagePicker from 'expo-image-picker';
import * as Location from 'expo-location';
import { StatusBar } from 'expo-status-bar';
import { useCallback, useEffect, useMemo, useState } from 'react';
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
import type {
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

const accessKey = 'workersbridge.access';
const refreshKey = 'workersbridge.refresh';
const maxUploadSize = 5 * 1024 * 1024;
const allowedImageTypes = ['image/jpeg', 'image/png', 'image/webp'];

type Session = {
  accessToken: string;
  refreshToken: string;
  user: User;
};

type Tab = 'home' | 'bookings' | 'messages' | 'profile' | 'support';

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

  const position = await Location.getCurrentPositionAsync({
    accuracy: Location.Accuracy.High,
  });
  const coords = {
    latitude: position.coords.latitude,
    longitude: position.coords.longitude,
  };
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
  const destinationLatitude = Number(booking.service_latitude);
  const destinationLongitude = Number(booking.service_longitude);
  if (!Number.isFinite(destinationLatitude) || !Number.isFinite(destinationLongitude) || !isValidCoordinate(destinationLatitude, destinationLongitude)) {
    Alert.alert('Location missing', 'This booking does not have a saved service location.');
    return;
  }

  try {
    const origin = await requestDeviceLocation();
    const url = googleMapsDirectionsUrl(origin, {
      latitude: destinationLatitude,
      longitude: destinationLongitude,
    });
    await Linking.openURL(url);
  } catch (error) {
    showError('Could not open directions', error);
  }
}

export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [booting, setBooting] = useState(true);

  useEffect(() => {
    async function restore() {
      const [[, accessToken], [, refreshToken]] = await AsyncStorage.multiGet([
        accessKey,
        refreshKey,
      ]);
      if (!accessToken || !refreshToken) {
        setBooting(false);
        return;
      }
      try {
        const user = await api.profile(accessToken);
        setSession({ accessToken, refreshToken, user });
      } catch {
        // Network/server errors should NOT destroy the session.
        // Only clear tokens if a refresh attempt also fails with a 401.
        try {
          const { access } = await api.refresh(refreshToken);
          const user = await api.profile(access);
          await AsyncStorage.setItem(accessKey, access);
          setSession({ accessToken: access, refreshToken, user });
        } catch {
          // If refresh also fails, keep session in a degraded state
          // rather than logging the user out on a network blip.
          // Only clear if we're confident the tokens are truly invalid.
        }
      } finally {
        setBooting(false);
      }
    }
    restore();
  }, []);

  const persistSession = useCallback(async (result: AuthResponse) => {
    await AsyncStorage.multiSet([
      [accessKey, result.access],
      [refreshKey, result.refresh],
    ]);
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

  if (!session) {
    return <AuthScreen onAuthenticated={persistSession} />;
  }

  return <MainApp session={session} updateSession={updateSession} logout={logout} />;
}

function AuthScreen({ onAuthenticated }: { onAuthenticated: (result: AuthResponse) => void }) {
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  const [role, setRole] = useState<SignupPayload['role']>('customer');
  const [otpSent, setOtpSent] = useState(false);
  const [emailForOtp, setEmailForOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [signupCoordinates, setSignupCoordinates] = useState<Coordinates | null>(null);
  const [locationPermissionGranted, setLocationPermissionGranted] = useState(false);
  const [locationMessage, setLocationMessage] = useState('');
  const [loginForm, setLoginForm] = useState({ email: '', password: '' });
  const [signupForm, setSignupForm] = useState({
    username: '',
    email: '',
    password: '',
    phone_number: '',
    location: '',
    email_otp: '',
  });

  async function login() {
    setLoading(true);
    try {
      const result = await api.login(loginForm.email.trim(), loginForm.password);
      await onAuthenticated(result);
    } catch (error) {
      showError('Login failed', error);
    } finally {
      setLoading(false);
    }
  }

  async function sendOtp() {
    setLoading(true);
    try {
      await api.sendSignupOtp(signupForm.email.trim());
      setEmailForOtp(signupForm.email.trim());
      setOtpSent(true);
      Alert.alert('OTP sent', 'Check your email for the verification code.');
    } catch (error) {
      showError('Could not send OTP', error);
    } finally {
      setLoading(false);
    }
  }

  async function signup() {
    setLoading(true);
    try {
      const result = await api.signup({
        username: signupForm.username.trim(),
        email: emailForOtp,
        password: signupForm.password,
        role,
        phone_number: signupForm.phone_number.trim(),
        location: signupForm.location.trim(),
        latitude: signupCoordinates ? parseFloat(signupCoordinates.latitude.toFixed(6)) : null,
        longitude: signupCoordinates ? parseFloat(signupCoordinates.longitude.toFixed(6)) : null,
        location_permission_granted: locationPermissionGranted,
        email_otp: signupForm.email_otp.trim(),
      });
      await onAuthenticated(result);
    } catch (error) {
      showError('Signup failed', error);
    } finally {
      setLoading(false);
    }
  }

  async function captureSignupLocation() {
    setLoading(true);
    try {
      const coords = await requestDeviceLocation();
      setSignupCoordinates(coords);
      setLocationPermissionGranted(true);
      setLocationMessage('Location saved for nearby services and jobs.');
    } catch (error) {
      setSignupCoordinates(null);
      setLocationPermissionGranted(false);
      setLocationMessage(error instanceof Error ? error.message : 'Location was not saved.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar style="dark" />
      <ScrollView contentContainerStyle={styles.authContent}>
        <View style={styles.brandBlock}>
          <Logo />
          <Text style={styles.heroTitle}>Reliable help. Real people.</Text>
          <Text style={styles.heroAccent}>Right when you need it.</Text>
          <Text style={styles.heroCopy}>
            Book skilled local workers, manage requests, upload portfolios, chat,
            and get support from one polished mobile app.
          </Text>
        </View>

        <View style={styles.segment}>
          <Pressable
            style={[styles.segmentButton, mode === 'login' && styles.segmentActive]}
            onPress={() => setMode('login')}
          >
            <Text style={[styles.segmentText, mode === 'login' && styles.segmentTextActive]}>
              Login
            </Text>
          </Pressable>
          <Pressable
            style={[styles.segmentButton, mode === 'signup' && styles.segmentActive]}
            onPress={() => setMode('signup')}
          >
            <Text style={[styles.segmentText, mode === 'signup' && styles.segmentTextActive]}>
              Create account
            </Text>
          </Pressable>
        </View>

        {mode === 'login' ? (
          <View style={styles.card}>
            <Input
              label="Email address"
              value={loginForm.email}
              onChangeText={(email) => setLoginForm((form) => ({ ...form, email }))}
              keyboardType="email-address"
              autoCapitalize="none"
            />
            <Input
              label="Password"
              value={loginForm.password}
              onChangeText={(password) => setLoginForm((form) => ({ ...form, password }))}
              secureTextEntry
            />
            <Button title={loading ? 'Signing in...' : 'Login'} onPress={login} disabled={loading} />
          </View>
        ) : (
          <View style={styles.card}>
            <View style={styles.roleRow}>
              <Pill
                label="Customer"
                active={role === 'customer'}
                onPress={() => setRole('customer')}
              />
              <Pill label="Worker" active={role === 'worker'} onPress={() => setRole('worker')} />
            </View>
            {!otpSent ? (
              <>
                <Text style={styles.sectionTitle}>Send OTP</Text>
                <Input
                  label="Email address"
                  value={signupForm.email}
                  onChangeText={(email) => setSignupForm((form) => ({ ...form, email }))}
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
                <Button title={loading ? 'Sending...' : 'Send OTP'} onPress={sendOtp} disabled={loading} />
              </>
            ) : (
              <>
                <Text style={styles.sectionTitle}>Verify email</Text>
                <Text style={styles.muted}>Code sent to {emailForOtp}</Text>
                <Input
                  label="Full name"
                  value={signupForm.username}
                  onChangeText={(username) => setSignupForm((form) => ({ ...form, username }))}
                />
                <Input
                  label="Phone"
                  value={signupForm.phone_number}
                  onChangeText={(phone_number) =>
                    setSignupForm((form) => ({ ...form, phone_number }))
                  }
                  keyboardType="phone-pad"
                />
                <Input
                  label="Location"
                  value={signupForm.location}
                  onChangeText={(location) => setSignupForm((form) => ({ ...form, location }))}
                />
                <View style={styles.locationBox}>
                  <Text style={styles.itemTitle}>GPS location</Text>
                  <Text style={styles.muted}>
                    Used only for location-based services and worker job directions.
                  </Text>
                  <GhostButton
                    title={signupCoordinates ? 'Update current location' : 'Use current location'}
                    onPress={captureSignupLocation}
                  />
                  {!!locationMessage && <Text style={styles.muted}>{locationMessage}</Text>}
                </View>
                <Input
                  label="Email OTP"
                  value={signupForm.email_otp}
                  onChangeText={(email_otp) => setSignupForm((form) => ({ ...form, email_otp }))}
                  keyboardType="number-pad"
                  maxLength={6}
                />
                <Input
                  label="Password"
                  value={signupForm.password}
                  onChangeText={(password) => setSignupForm((form) => ({ ...form, password }))}
                  secureTextEntry
                />
                <Button title={loading ? 'Creating...' : 'Continue'} onPress={signup} disabled={loading} />
                <GhostButton title="Use a different email" onPress={() => setOtpSent(false)} />
              </>
            )}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

function MainApp({ session, updateSession, logout }: ScreenProps) {
  const [tab, setTab] = useState<Tab>('home');
  const title = tab === 'home' ? (session.user.role === 'worker' ? 'Worker dashboard' : 'Find workers') : labelize(tab);

  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar style="dark" />
      <View style={styles.appHeader}>
        <View>
          <Text style={styles.eyebrow}>{session.user.role}</Text>
          <Text style={styles.title}>{title}</Text>
        </View>
        <View style={styles.headerActions}>
          <Pressable style={styles.iconButton} onPress={() => setTab('messages')}>
            <Text style={styles.iconText}>M</Text>
          </Pressable>
          <Pressable onPress={() => setTab('profile')}>
            <Avatar user={session.user} size={44} />
          </Pressable>
        </View>
      </View>

      <ScrollView contentContainerStyle={styles.content}>
        {tab === 'home' &&
          (session.user.role === 'worker' ? (
            <WorkerHome session={session} updateSession={updateSession} logout={logout} />
          ) : (
            <CustomerHome session={session} updateSession={updateSession} logout={logout} />
          ))}
        {tab === 'bookings' && (
          <BookingsScreen session={session} updateSession={updateSession} logout={logout} />
        )}
        {tab === 'messages' && (
          <MessagesScreen session={session} updateSession={updateSession} logout={logout} />
        )}
        {tab === 'profile' && (
          <ProfileScreen session={session} updateSession={updateSession} logout={logout} />
        )}
        {tab === 'support' && (
          <SupportScreen session={session} updateSession={updateSession} logout={logout} />
        )}
      </ScrollView>

      <View style={styles.tabbar}>
        <TabButton label="Home" icon="H" active={tab === 'home'} onPress={() => setTab('home')} />
        <TabButton label="Bookings" icon="B" active={tab === 'bookings'} onPress={() => setTab('bookings')} />
        <TabButton label="Messages" icon="M" active={tab === 'messages'} onPress={() => setTab('messages')} />
        <TabButton label="Profile" icon="P" active={tab === 'profile'} onPress={() => setTab('profile')} />
        <TabButton label="Support" icon="S" active={tab === 'support'} onPress={() => setTab('support')} />
      </View>
    </SafeAreaView>
  );
}

function CustomerHome({ session }: ScreenProps) {
  const [categories, setCategories] = useState<CategorySummary[]>([]);
  const [workers, setWorkers] = useState<WorkerProfile[]>([]);
  const [selectedWorker, setSelectedWorker] = useState<WorkerProfile | null>(null);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [availableOnly, setAvailableOnly] = useState(true);
  const [serviceCoordinates, setServiceCoordinates] = useState<Coordinates | null>(null);
  const [serviceLocationMessage, setServiceLocationMessage] = useState('');
  const [bookingForm, setBookingForm] = useState({
    scheduled_at: '',
    address: session.user.location ?? '',
    description: '',
  });

  const loadBookings = useCallback(() => {
    api.customerBookings(session.accessToken).then((result) => setBookings(result.list)).catch(() => undefined);
  }, [session.accessToken]);

  useEffect(() => {
    api.categories().then((result) => setCategories(result.list)).catch(() => undefined);
    loadBookings();
  }, [loadBookings]);

  useEffect(() => {
    api
      .nearbyWorkers({ category, search, availableOnly })
      .then((result) => {
        setWorkers(result.list);
        setSelectedWorker((current) => current ?? result.list[0] ?? null);
      })
      .catch((error) => showError('Could not load workers', error));
  }, [availableOnly, category, search]);

  async function bookService() {
    if (!selectedWorker) return;
    try {
      const scheduledAt = parseSchedule(bookingForm.scheduled_at);
      const booking = await api.createBooking(session.accessToken, {
        worker_id: selectedWorker.id,
        service_category: selectedWorker.category,
        description: bookingForm.description,
        address: bookingForm.address || session.user.location || '',
        service_latitude: serviceCoordinates?.latitude ?? null,
        service_longitude: serviceCoordinates?.longitude ?? null,
        location_permission_granted: Boolean(serviceCoordinates),
        scheduled_at: scheduledAt,
        total_amount: selectedWorker.price,
      });
      setBookings((current) => [booking, ...current]);
      setBookingForm({ scheduled_at: '', address: session.user.location ?? '', description: '' });
      setServiceCoordinates(null);
      setServiceLocationMessage('');
      Alert.alert('Booking sent', 'Your booking request has been submitted.');
    } catch (error) {
      showError('Could not create booking', error);
    }
  }

  async function captureServiceLocation() {
    try {
      const coords = await requestDeviceLocation();
      setServiceCoordinates(coords);
      setServiceLocationMessage('Service location saved for this booking.');
    } catch (error) {
      setServiceCoordinates(null);
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
          <Switch
            value={availableOnly}
            onValueChange={setAvailableOnly}
            trackColor={{ false: palette.line, true: palette.primarySoft }}
            thumbColor={availableOnly ? palette.primary : '#F4F4F5'}
          />
        </View>
        <Input label="Search" value={search} onChangeText={setSearch} placeholder="Service, worker, or location" />
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRow}>
          <Pill label="All" active={!category} onPress={() => setCategory('')} />
          {categories.slice(0, 8).map((item) => (
            <Pill
              key={item.category}
              label={item.category}
              active={category === item.category}
              onPress={() => setCategory(item.category)}
            />
          ))}
        </ScrollView>
      </View>

      {workers.map((worker) => (
        <Pressable
          key={worker.id}
          style={[styles.workerCard, selectedWorker?.id === worker.id && styles.selectedCard]}
          onPress={() => setSelectedWorker(worker)}
        >
          <Avatar user={worker.user} size={58} />
          <View style={styles.flex}>
            <Text style={styles.itemTitle}>{worker.user.username}</Text>
            <Text style={styles.muted}>{worker.category}</Text>
            <Text style={styles.rating}>Rating {worker.rating} ({worker.total_reviews})</Text>
          </View>
          <View style={styles.rightMeta}>
            <Text style={styles.price}>{money(worker.price)}</Text>
            <Text style={styles.online}>{worker.is_online ? 'Available' : 'Offline'}</Text>
          </View>
        </Pressable>
      ))}

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Book service</Text>
        {selectedWorker ? (
          <>
            <Text style={styles.itemTitle}>{selectedWorker.user.username} - {selectedWorker.category}</Text>
            <Input
              label="Schedule"
              value={bookingForm.scheduled_at}
              onChangeText={(scheduled_at) => setBookingForm((form) => ({ ...form, scheduled_at }))}
              placeholder="2026-08-08 18:30"
            />
            <Input
              label="Address"
              value={bookingForm.address}
              onChangeText={(address) => setBookingForm((form) => ({ ...form, address }))}
            />
            <View style={styles.locationBox}>
              <Text style={styles.itemTitle}>Service location</Text>
              <Text style={styles.muted}>
                Save the exact job location for worker navigation.
              </Text>
              <GhostButton
                title={serviceCoordinates ? 'Update service location' : 'Use current service location'}
                onPress={captureServiceLocation}
              />
              {!!serviceLocationMessage && <Text style={styles.muted}>{serviceLocationMessage}</Text>}
            </View>
            <Input
              label="Describe your job"
              value={bookingForm.description}
              onChangeText={(description) => setBookingForm((form) => ({ ...form, description }))}
              multiline
            />
            <Button title="Confirm booking" onPress={bookService} />
          </>
        ) : (
          <EmptyState title="No worker selected" text="Choose a worker to create a booking." />
        )}
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>My bookings</Text>
        {bookings.slice(0, 3).map((booking) => (
          <BookingCard key={booking.id} booking={booking} />
        ))}
        {!bookings.length && <EmptyState title="No bookings yet" text="Your recent bookings appear here." />}
      </View>
    </>
  );
}

function WorkerHome({ session }: ScreenProps) {
  const [summary, setSummary] = useState<WorkerDashboardSummary | null>(null);
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [jobCategories, setJobCategories] = useState<string[]>([]);
  const [profileForm, setProfileForm] = useState({
    category: '',
    price: '',
    experience_years: '1',
    bio: '',
    is_online: true,
  });

  const profile = summary?.profile;

  const loadWorker = useCallback(() => {
    api.workerDashboard(session.accessToken)
      .then((result) => {
        setSummary(result);
        setProfileForm({
          category: result.profile.category,
          price: result.profile.price,
          experience_years: String(result.profile.experience_years),
          bio: result.profile.bio,
          is_online: result.profile.is_online,
        });
      })
      .catch(() => undefined);
    api.workerBookings(session.accessToken).then((result) => setBookings(result.list)).catch(() => undefined);
  }, [session.accessToken]);

  useEffect(() => {
    loadWorker();
    api.jobCategories().then((result) => setJobCategories(result.list)).catch(() => undefined);
  }, [loadWorker]);

  async function saveProfile() {
    try {
      const saved = await api.saveWorkerProfile(session.accessToken, {
        category: profileForm.category,
        price: profileForm.price,
        experience_years: Number(profileForm.experience_years),
        bio: profileForm.bio,
        is_online: profileForm.is_online,
      });
      setSummary((current) => current && { ...current, profile: saved });
      Alert.alert('Saved', 'Worker profile updated.');
    } catch (error) {
      showError('Could not save worker profile', error);
    }
  }

  async function updateAvailability(value: boolean) {
    try {
      const saved = await api.updateAvailability(session.accessToken, value);
      setSummary((current) => current && { ...current, profile: saved });
      setProfileForm((form) => ({ ...form, is_online: saved.is_online }));
    } catch (error) {
      showError('Could not update availability', error);
    }
  }

  async function updateStatus(bookingId: number, status: BookingStatus) {
    try {
      const updated = await api.updateBookingStatus(session.accessToken, bookingId, status);
      setBookings((current) => current.map((booking) => (booking.id === bookingId ? updated : booking)));
    } catch (error) {
      showError('Could not update booking', error);
    }
  }

  async function uploadPortfolio() {
    if (!profile) {
      Alert.alert('Create profile first', 'Save your worker profile before uploading portfolio images.');
      return;
    }
    const image = await pickImage();
    if (!image) return;
    const formData = new FormData();
    formData.append('images', image as unknown as Blob);
    formData.append('caption', 'Portfolio work');
    try {
      await api.uploadWorkImages(session.accessToken, formData);
      loadWorker();
      Alert.alert('Uploaded', 'Portfolio image uploaded.');
    } catch (error) {
      showError('Could not upload portfolio image', error);
    }
  }

  async function deletePortfolioImage(imageId: number) {
    try {
      await api.deleteWorkImage(session.accessToken, imageId);
      loadWorker();
    } catch (error) {
      showError('Could not delete image', error);
    }
  }

  return (
    <>
      <View style={styles.card}>
        <View style={styles.row}>
          <View style={styles.flex}>
            <Text style={styles.sectionTitle}>{session.user.username}</Text>
            <Text style={styles.muted}>{profile?.category || 'Set up your worker profile'}</Text>
          </View>
          <Switch
            value={profileForm.is_online}
            onValueChange={updateAvailability}
            trackColor={{ false: palette.line, true: palette.primarySoft }}
            thumbColor={profileForm.is_online ? palette.primary : '#F4F4F5'}
          />
        </View>
      </View>

      <View style={styles.metricsGrid}>
        <Metric label="Pending" value={summary?.metrics.pending_requests ?? 0} />
        <Metric label="Active" value={summary?.metrics.active_jobs ?? 0} />
        <Metric label="Done" value={summary?.metrics.completed_jobs ?? 0} />
        <Metric label="Earnings" value={money(summary?.metrics.total_earnings ?? '0')} />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Booking requests</Text>
        <GhostButton title="Refresh" onPress={loadWorker} />
        {bookings.slice(0, 5).map((booking) => (
          <View key={booking.id} style={styles.bookingCard}>
            <BookingCard booking={booking} />
            <View style={styles.actionRow}>
              <SmallButton
                title="Get Directions"
                onPress={() => openDirectionsForBooking(booking)}
                variant="ghost"
              />
              {booking.status === 'requested' && (
                <>
                  <SmallButton title="Accept" onPress={() => updateStatus(booking.id, 'accepted')} />
                  <SmallButton title="Decline" onPress={() => updateStatus(booking.id, 'declined')} variant="ghost" />
                </>
              )}
              {booking.status === 'accepted' && (
                <SmallButton title="On the way" onPress={() => updateStatus(booking.id, 'on_the_way')} />
              )}
              {['accepted', 'on_the_way'].includes(booking.status) && (
                <SmallButton title="Start" onPress={() => updateStatus(booking.id, 'in_progress')} variant="ghost" />
              )}
              {booking.status === 'in_progress' && (
                <SmallButton title="Complete" onPress={() => updateStatus(booking.id, 'completed')} />
              )}
            </View>
          </View>
        ))}
        {!bookings.length && <EmptyState title="No requests" text="Customer requests appear here." />}
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Profile setup</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRow}>
          {jobCategories.map((item) => (
            <Pill
              key={item}
              label={item}
              active={profileForm.category === item}
              onPress={() => setProfileForm((form) => ({ ...form, category: item }))}
            />
          ))}
        </ScrollView>
        <Input
          label="Category"
          value={profileForm.category}
          onChangeText={(category) => setProfileForm((form) => ({ ...form, category }))}
        />
        <Input
          label="Hourly rate"
          value={profileForm.price}
          onChangeText={(price) => setProfileForm((form) => ({ ...form, price }))}
          keyboardType="decimal-pad"
        />
        <Input
          label="Experience years"
          value={profileForm.experience_years}
          onChangeText={(experience_years) =>
            setProfileForm((form) => ({ ...form, experience_years }))
          }
          keyboardType="number-pad"
        />
        <Input
          label="Bio"
          value={profileForm.bio}
          onChangeText={(bio) => setProfileForm((form) => ({ ...form, bio }))}
          multiline
        />
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
                <Text style={styles.deleteText}>x</Text>
              </Pressable>
            </View>
          ))}
        </View>
        {!profile?.work_images.length && (
          <EmptyState title="No photos" text="Upload work photos after creating your profile." />
        )}
      </View>
    </>
  );
}

function BookingsScreen({ session }: ScreenProps) {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [status, setStatus] = useState<BookingStatus | ''>('');
  const [reviewingId, setReviewingId] = useState<number | null>(null);
  const [review, setReview] = useState({ rating: '5', feedback: '' });
  const isWorker = session.user.role === 'worker';

  const loadBookings = useCallback(() => {
    const request = isWorker
      ? api.workerBookings(session.accessToken, status || undefined)
      : api.customerBookings(session.accessToken, status || undefined);
    request.then((result) => setBookings(result.list)).catch((error) => showError('Could not load bookings', error));
  }, [isWorker, session.accessToken, status]);

  useEffect(() => {
    loadBookings();
  }, [loadBookings]);

  async function submitReview(bookingId: number) {
    try {
      await api.createReview(session.accessToken, bookingId, Number(review.rating), review.feedback);
      setBookings((current) =>
        current.map((booking) => (booking.id === bookingId ? { ...booking, has_review: true } : booking)),
      );
      setReviewingId(null);
      setReview({ rating: '5', feedback: '' });
      Alert.alert('Submitted', 'Review submitted.');
    } catch (error) {
      showError('Could not submit review', error);
    }
  }

  async function updateStatus(bookingId: number, nextStatus: BookingStatus) {
    try {
      const updated = await api.updateBookingStatus(session.accessToken, bookingId, nextStatus);
      setBookings((current) =>
        current.map((booking) => (booking.id === bookingId ? updated : booking)),
      );
    } catch (error) {
      showError('Could not update booking', error);
    }
  }

  return (
    <View style={styles.card}>
      <View style={styles.row}>
        <Text style={styles.sectionTitle}>{isWorker ? 'Requests and jobs' : 'My bookings'}</Text>
        <GhostButton title="Refresh" onPress={loadBookings} />
      </View>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.chipRow}>
        <Pill label="All" active={!status} onPress={() => setStatus('')} />
        {(['requested', 'accepted', 'on_the_way', 'in_progress', 'completed', 'cancelled', 'declined'] as BookingStatus[]).map((item) => (
          <Pill key={item} label={labelize(item)} active={status === item} onPress={() => setStatus(item)} />
        ))}
      </ScrollView>
      {bookings.map((booking) => (
        <View key={booking.id} style={styles.bookingCard}>
          <BookingCard booking={booking} />
          {isWorker && (
            <View style={styles.actionRow}>
              <SmallButton
                title="Get Directions"
                onPress={() => openDirectionsForBooking(booking)}
                variant="ghost"
              />
              {booking.status === 'requested' && (
                <>
                  <SmallButton title="Accept" onPress={() => updateStatus(booking.id, 'accepted')} />
                  <SmallButton title="Decline" onPress={() => updateStatus(booking.id, 'declined')} variant="ghost" />
                </>
              )}
              {booking.status === 'accepted' && (
                <SmallButton title="On the way" onPress={() => updateStatus(booking.id, 'on_the_way')} />
              )}
              {['accepted', 'on_the_way'].includes(booking.status) && (
                <SmallButton title="Start" onPress={() => updateStatus(booking.id, 'in_progress')} variant="ghost" />
              )}
              {booking.status === 'in_progress' && (
                <SmallButton title="Complete" onPress={() => updateStatus(booking.id, 'completed')} />
              )}
            </View>
          )}
          {!isWorker && booking.status === 'completed' && !booking.has_review && (
            <>
              <SmallButton title="Review" onPress={() => setReviewingId(booking.id)} />
              {reviewingId === booking.id && (
                <View style={styles.reviewBox}>
                  <Input
                    label="Rating"
                    value={review.rating}
                    onChangeText={(rating) => setReview((form) => ({ ...form, rating }))}
                    keyboardType="number-pad"
                  />
                  <Input
                    label="Feedback"
                    value={review.feedback}
                    onChangeText={(feedback) => setReview((form) => ({ ...form, feedback }))}
                    multiline
                  />
                  <Button title="Submit review" onPress={() => submitReview(booking.id)} />
                </View>
              )}
            </>
          )}
        </View>
      ))}
      {!bookings.length && <EmptyState title="No bookings" text="Bookings matching this filter appear here." />}
    </View>
  );
}

function MessagesScreen({ session }: ScreenProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [text, setText] = useState('');

  const loadConversations = useCallback(() => {
    api.conversations(session.accessToken)
      .then((result) => {
        setConversations(result.list);
        setSelectedConversation((current) => {
          if (!current) return null;
          return result.list.find((conversation) => conversation.id === current.id) ?? null;
        });
      })
      .catch((error) => showError('Could not load conversations', error));
  }, [session.accessToken]);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  useEffect(() => {
    if (!selectedConversation) {
      setMessages([]);
      return;
    }
    api
      .messages(session.accessToken, selectedConversation.id)
      .then((result) => setMessages(result.list))
      .catch(() => undefined);
  }, [selectedConversation, session.accessToken]);

  async function sendMessage() {
    if (!selectedConversation || !text.trim()) return;
    try {
      const message = await api.sendMessage(session.accessToken, selectedConversation.id, text.trim());
      setMessages((current) => [...current, message]);
      setText('');
      loadConversations();
    } catch (error) {
      showError('Could not send message', error);
    }
  }

  if (selectedConversation) {
    return (
      <View style={styles.chatPage}>
        <View style={styles.chatHeader}>
          <Pressable
            style={styles.backButton}
            onPress={() => {
              setSelectedConversation(null);
              setText('');
            }}
          >
            <Text style={styles.backButtonText}>Back</Text>
          </Pressable>
          <View style={styles.flex}>
            <Text style={styles.sectionTitle}>{selectedConversation.other_party_name}</Text>
            <Text style={styles.muted} numberOfLines={1}>
              {selectedConversation.booking.service_category} - {selectedConversation.booking.status_display}
            </Text>
          </View>
        </View>

        <View style={styles.chatBody}>
          {messages.map((message) => (
            <View
              key={message.id}
              style={[styles.messageRow, message.sender.id === session.user.id && styles.myMessageRow]}
            >
              <View
                style={[
                  styles.bubble,
                  message.sender.id === session.user.id && styles.myBubble,
                ]}
              >
                <Text
                  style={
                    message.sender.id === session.user.id
                      ? styles.myBubbleText
                      : styles.bubbleText
                  }
                >
                  {message.text}
                </Text>
                <Text
                  style={
                    message.sender.id === session.user.id
                      ? styles.myBubbleTime
                      : styles.bubbleTime
                  }
                >
                  {formatDate(message.created_at)}
                </Text>
              </View>
            </View>
          ))}
          {!messages.length && (
            <EmptyState title="No messages yet" text="Start the conversation from here." />
          )}
        </View>

        <View style={styles.composer}>
          <TextInput
            onChangeText={setText}
            placeholder="Write a message"
            placeholderTextColor={palette.muted}
            style={styles.composerInput}
            value={text}
          />
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
          <Pressable
            key={conversation.id}
            style={styles.conversationRow}
            onPress={() => setSelectedConversation(conversation)}
          >
            <View style={styles.conversationAvatar}>
              <Text style={styles.conversationAvatarText}>
                {conversation.other_party_name.slice(0, 1).toUpperCase()}
              </Text>
            </View>
            <View style={styles.flex}>
              <Text style={styles.itemTitle}>{conversation.other_party_name}</Text>
              <Text style={styles.muted} numberOfLines={1}>
                {conversation.last_message?.text ?? 'No messages yet'}
              </Text>
              <Text style={styles.conversationMeta} numberOfLines={1}>
                {conversation.booking.service_category} - {conversation.booking.status_display}
              </Text>
            </View>
            {!!conversation.unread_count && <Text style={styles.badge}>{conversation.unread_count}</Text>}
          </Pressable>
        ))}
        {!conversations.length && <EmptyState title="No conversations" text="Chats are created after booking." />}
      </View>
  );
}

function ProfileScreen({ session, updateSession, logout }: ScreenProps) {
  const [profileForm, setProfileForm] = useState({
    username: session.user.username,
    email: session.user.email,
    phone_number: session.user.phone_number ?? '',
    location: session.user.location ?? '',
  });
  const [passwordForm, setPasswordForm] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  });
  const [photo, setPhoto] = useState<PickedImage | null>(null);

  async function chooseProfilePhoto() {
    const image = await pickImage();
    if (image) setPhoto(image);
  }

  async function saveProfile() {
    const formData = new FormData();
    formData.append('username', profileForm.username);
    formData.append('email', profileForm.email);
    formData.append('phone_number', profileForm.phone_number);
    formData.append('location', profileForm.location);
    if (photo) formData.append('profile_photo', photo as unknown as Blob);

    try {
      const user = await api.updateProfileForm(session.accessToken, formData);
      updateSession({ ...session, user });
      setPhoto(null);
      Alert.alert('Saved', 'Profile updated.');
    } catch (error) {
      showError('Could not update profile', error);
    }
  }

  async function changePassword() {
    try {
      await api.changePassword(
        session.accessToken,
        passwordForm.old_password,
        passwordForm.new_password,
        passwordForm.confirm_password,
      );
      setPasswordForm({ old_password: '', new_password: '', confirm_password: '' });
      Alert.alert('Saved', 'Password changed.');
    } catch (error) {
      showError('Could not change password', error);
    }
  }

  return (
    <>
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Edit profile</Text>
        <View style={styles.profilePhotoRow}>
          <Avatar user={{ ...session.user, profile_photo_url: photo?.uri ?? session.user.profile_photo_url }} size={76} />
          <GhostButton title="Choose photo" onPress={chooseProfilePhoto} />
        </View>
        <Input label="Full name" value={profileForm.username} onChangeText={(username) => setProfileForm((form) => ({ ...form, username }))} />
        <Input label="Email" value={profileForm.email} onChangeText={(email) => setProfileForm((form) => ({ ...form, email }))} keyboardType="email-address" autoCapitalize="none" />
        <Input label="Phone" value={profileForm.phone_number} onChangeText={(phone_number) => setProfileForm((form) => ({ ...form, phone_number }))} keyboardType="phone-pad" />
        <Input label="Location" value={profileForm.location} onChangeText={(location) => setProfileForm((form) => ({ ...form, location }))} />
        <Button title="Save profile" onPress={saveProfile} />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Change password</Text>
        <Input label="Old password" value={passwordForm.old_password} onChangeText={(old_password) => setPasswordForm((form) => ({ ...form, old_password }))} secureTextEntry />
        <Input label="New password" value={passwordForm.new_password} onChangeText={(new_password) => setPasswordForm((form) => ({ ...form, new_password }))} secureTextEntry />
        <Input label="Confirm password" value={passwordForm.confirm_password} onChangeText={(confirm_password) => setPasswordForm((form) => ({ ...form, confirm_password }))} secureTextEntry />
        <Button title="Update password" onPress={changePassword} />
      </View>

      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Session</Text>
        <GhostButton title="Log out" onPress={logout} />
      </View>
    </>
  );
}

function SupportScreen({ session }: ScreenProps) {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [ticketForm, setTicketForm] = useState({ subject: '', message: '' });

  const loadTickets = useCallback(() => {
    api.supportTickets(session.accessToken).then((result) => setTickets(result.list)).catch(() => undefined);
  }, [session.accessToken]);

  useEffect(() => {
    loadTickets();
  }, [loadTickets]);

  async function submitTicket() {
    try {
      const ticket = await api.createSupportTicket(
        session.accessToken,
        ticketForm.subject,
        ticketForm.message,
      );
      setTickets((current) => [ticket, ...current]);
      setTicketForm({ subject: '', message: '' });
      Alert.alert('Submitted', 'Support ticket submitted.');
    } catch (error) {
      showError('Could not submit ticket', error);
    }
  }

  return (
    <>
      <View style={styles.card}>
        <Text style={styles.sectionTitle}>Help and support</Text>
        <Input label="Subject" value={ticketForm.subject} onChangeText={(subject) => setTicketForm((form) => ({ ...form, subject }))} />
        <Input label="Message" value={ticketForm.message} onChangeText={(message) => setTicketForm((form) => ({ ...form, message }))} multiline />
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

function Input(props: {
  label: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder?: string;
  secureTextEntry?: boolean;
  keyboardType?: 'default' | 'email-address' | 'number-pad' | 'phone-pad' | 'decimal-pad';
  autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters';
  multiline?: boolean;
  maxLength?: number;
}) {
  return (
    <View style={styles.inputGroup}>
      <Text style={styles.inputLabel}>{props.label}</Text>
      <TextInput
        autoCapitalize={props.autoCapitalize}
        keyboardType={props.keyboardType}
        maxLength={props.maxLength}
        multiline={props.multiline}
        onChangeText={props.onChangeText}
        placeholder={props.placeholder}
        placeholderTextColor={palette.muted}
        secureTextEntry={props.secureTextEntry}
        style={[styles.input, props.multiline && styles.multiline]}
        textAlignVertical={props.multiline ? 'top' : 'center'}
        value={props.value}
      />
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

function SmallButton({
  title,
  onPress,
  variant,
}: {
  title: string;
  onPress: () => void;
  variant?: 'ghost';
}) {
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

function TabButton({
  label,
  icon,
  active,
  onPress,
}: {
  label: string;
  icon: string;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <Pressable style={styles.tabButton} onPress={onPress}>
      <Text style={[styles.tabIcon, active && styles.tabActive]}>{icon}</Text>
      <Text style={[styles.tabText, active && styles.tabActive]} numberOfLines={1}>
        {label}
      </Text>
    </Pressable>
  );
}

function Logo() {
  return (
    <View style={styles.logo}>
      <View style={styles.logoMark}>
        <Text style={styles.logoMarkText}>WB</Text>
      </View>
      <Text style={styles.logoText}>WorkersBridge</Text>
    </View>
  );
}

function Avatar({ user, size }: { user: User; size: number }) {
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
    return <Image source={{ uri: user.profile_photo_url }} style={[styles.avatar, { height: size, width: size }]} />;
  }

  return (
    <View style={[styles.avatar, styles.avatarFallback, { height: size, width: size }]}>
      <Text style={styles.avatarText}>{initials}</Text>
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

function BookingCard({ booking }: { booking: Booking }) {
  return (
    <View style={styles.bookingInner}>
      <View style={styles.row}>
        <View style={styles.flex}>
          <Text style={styles.itemTitle}>{booking.service_category}</Text>
          <Text style={styles.muted}>{booking.worker.user.username}</Text>
        </View>
        <Text style={styles.price}>{money(booking.total_amount)}</Text>
      </View>
      <Text style={styles.muted}>{booking.address}</Text>
      <View style={styles.row}>
        <Text style={styles.muted}>{formatDate(booking.scheduled_at)}</Text>
        <Text style={[styles.status, statusStyle(booking.status)]}>{booking.status_display}</Text>
      </View>
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
  return {
    uri: asset.uri,
    name: asset.fileName || `upload.${extensionFromMime(type)}`,
    type,
    size: asset.fileSize,
  };
}

function showError(title: string, error: unknown) {
  Alert.alert(title, error instanceof Error ? error.message : 'Try again.');
}

function parseSchedule(value: string) {
  const normalized = value.trim().replace(' ', 'T');
  const date = new Date(normalized);
  if (Number.isNaN(date.getTime())) {
    throw new Error('Enter schedule as YYYY-MM-DD HH:mm.');
  }
  return date.toISOString();
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

function mimeFromUri(uri: string) {
  const extension = uri.split('.').pop()?.toLowerCase();
  if (extension === 'jpg' || extension === 'jpeg') return 'image/jpeg';
  if (extension === 'webp') return 'image/webp';
  return 'image/png';
}

function extensionFromMime(mime: string) {
  if (mime === 'image/jpeg') return 'jpg';
  if (mime === 'image/webp') return 'webp';
  return 'png';
}

function statusStyle(status: BookingStatus) {
  if (status === 'completed') return styles.statusAmber;
  if (status === 'cancelled' || status === 'declined') return styles.statusDanger;
  return styles.statusPrimary;
}

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
};

const styles = StyleSheet.create({
  screen: {
    backgroundColor: palette.bg,
    flex: 1,
  },
  center: {
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
  },
  authContent: {
    gap: 18,
    padding: 20,
  },
  content: {
    gap: 14,
    padding: 16,
    paddingBottom: 92,
  },
  brandBlock: {
    backgroundColor: '#FBF7EF',
    borderColor: palette.line,
    borderRadius: 8,
    borderWidth: 1,
    gap: 10,
    padding: 18,
  },
  logo: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  logoMark: {
    alignItems: 'center',
    backgroundColor: palette.primary,
    borderRadius: 8,
    height: 38,
    justifyContent: 'center',
    width: 38,
  },
  logoMarkText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '900',
  },
  logoText: {
    color: palette.text,
    fontSize: 20,
    fontWeight: '900',
  },
  heroTitle: {
    color: palette.text,
    fontSize: 31,
    fontWeight: '900',
    lineHeight: 35,
    marginTop: 8,
  },
  heroAccent: {
    color: palette.primaryStrong,
    fontSize: 29,
    fontWeight: '900',
  },
  heroCopy: {
    color: '#33443F',
    fontSize: 15,
    lineHeight: 22,
  },
  segment: {
    backgroundColor: palette.surface,
    borderColor: palette.line,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: 'row',
    padding: 4,
  },
  segmentButton: {
    alignItems: 'center',
    borderRadius: 8,
    flex: 1,
    padding: 12,
  },
  segmentActive: {
    backgroundColor: palette.primarySoft,
  },
  segmentText: {
    color: palette.muted,
    fontWeight: '900',
  },
  segmentTextActive: {
    color: palette.primaryStrong,
  },
  card: {
    backgroundColor: palette.surface,
    borderColor: palette.line,
    borderRadius: 8,
    borderWidth: 1,
    gap: 12,
    padding: 14,
  },
  appHeader: {
    alignItems: 'center',
    backgroundColor: palette.surface,
    borderBottomColor: palette.line,
    borderBottomWidth: 1,
    flexDirection: 'row',
    justifyContent: 'space-between',
    padding: 16,
  },
  headerActions: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 10,
  },
  iconButton: {
    alignItems: 'center',
    backgroundColor: palette.primarySoft,
    borderRadius: 8,
    height: 42,
    justifyContent: 'center',
    width: 42,
  },
  iconText: {
    fontSize: 18,
  },
  eyebrow: {
    color: palette.primary,
    fontSize: 11,
    fontWeight: '900',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  title: {
    color: palette.text,
    fontSize: 25,
    fontWeight: '900',
  },
  sectionTitle: {
    color: palette.text,
    fontSize: 19,
    fontWeight: '900',
  },
  itemTitle: {
    color: palette.text,
    fontSize: 15,
    fontWeight: '900',
  },
  muted: {
    color: palette.muted,
    fontSize: 13,
    lineHeight: 19,
  },
  mutedStrong: {
    color: palette.muted,
    fontWeight: '900',
  },
  inputGroup: {
    gap: 6,
  },
  inputLabel: {
    color: palette.text,
    fontSize: 13,
    fontWeight: '900',
  },
  input: {
    backgroundColor: palette.surface,
    borderColor: palette.line,
    borderRadius: 8,
    borderWidth: 1,
    color: palette.text,
    paddingHorizontal: 13,
    paddingVertical: 12,
  },
  multiline: {
    minHeight: 92,
  },
  button: {
    alignItems: 'center',
    backgroundColor: palette.primary,
    borderRadius: 8,
    padding: 14,
  },
  disabled: {
    opacity: 0.62,
  },
  buttonText: {
    color: '#FFFFFF',
    fontWeight: '900',
  },
  ghostButton: {
    alignItems: 'center',
    backgroundColor: palette.primarySoft,
    borderRadius: 8,
    paddingHorizontal: 13,
    paddingVertical: 10,
  },
  ghostText: {
    color: palette.primaryStrong,
    fontWeight: '900',
  },
  smallButton: {
    alignItems: 'center',
    backgroundColor: palette.primary,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 9,
  },
  smallButtonText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '900',
  },
  smallGhost: {
    backgroundColor: palette.surfaceSoft,
  },
  smallGhostText: {
    color: palette.primaryStrong,
  },
  roleRow: {
    flexDirection: 'row',
    gap: 10,
  },
  chipRow: {
    gap: 9,
  },
  pill: {
    backgroundColor: palette.surface,
    borderColor: palette.line,
    borderRadius: 8,
    borderWidth: 1,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  pillActive: {
    backgroundColor: palette.primarySoft,
    borderColor: palette.primary,
  },
  pillText: {
    color: palette.text,
    fontWeight: '900',
  },
  pillTextActive: {
    color: palette.primaryStrong,
  },
  row: {
    alignItems: 'center',
    flexDirection: 'row',
    gap: 12,
    justifyContent: 'space-between',
  },
  flex: {
    flex: 1,
  },
  workerCard: {
    alignItems: 'center',
    backgroundColor: palette.surface,
    borderColor: palette.line,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 12,
    padding: 12,
  },
  selectedCard: {
    backgroundColor: '#F4FFFB',
    borderColor: palette.primary,
  },
  rating: {
    color: palette.amber,
    fontSize: 12,
    fontWeight: '900',
    marginTop: 4,
  },
  rightMeta: {
    alignItems: 'flex-end',
  },
  price: {
    color: palette.text,
    fontSize: 16,
    fontWeight: '900',
  },
  online: {
    color: palette.primaryStrong,
    fontSize: 12,
    fontWeight: '900',
  },
  metricsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
  },
  metric: {
    backgroundColor: palette.surface,
    borderColor: palette.line,
    borderRadius: 8,
    borderWidth: 1,
    flexBasis: '47%',
    flexGrow: 1,
    padding: 14,
  },
  metricValue: {
    color: palette.text,
    fontSize: 22,
    fontWeight: '900',
  },
  metricLabel: {
    color: palette.muted,
    fontSize: 12,
    marginTop: 4,
  },
  bookingCard: {
    borderColor: palette.line,
    borderRadius: 8,
    borderWidth: 1,
    gap: 10,
    padding: 10,
  },
  bookingInner: {
    gap: 8,
  },
  actionRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  status: {
    borderRadius: 999,
    fontSize: 11,
    fontWeight: '900',
    paddingHorizontal: 9,
    paddingVertical: 5,
    textTransform: 'uppercase',
  },
  statusPrimary: {
    backgroundColor: palette.primarySoft,
    color: palette.primaryStrong,
  },
  statusAmber: {
    backgroundColor: '#FFF3CF',
    color: '#915D00',
  },
  statusDanger: {
    backgroundColor: '#FFF1F2',
    color: palette.danger,
  },
  imageGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  portfolioItem: {
    position: 'relative',
  },
  portfolioImage: {
    backgroundColor: palette.surfaceSoft,
    borderRadius: 8,
    height: 96,
    width: 96,
  },
  deleteButton: {
    alignItems: 'center',
    backgroundColor: 'rgba(17,24,39,0.82)',
    borderRadius: 8,
    height: 28,
    justifyContent: 'center',
    position: 'absolute',
    right: 4,
    top: 4,
    width: 28,
  },
  deleteText: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '900',
  },
  reviewBox: {
    backgroundColor: palette.surfaceSoft,
    borderRadius: 8,
    gap: 10,
    padding: 10,
  },
  locationBox: {
    backgroundColor: palette.surfaceSoft,
    borderColor: palette.line,
    borderRadius: 8,
    borderWidth: 1,
    gap: 8,
    padding: 12,
  },
  conversationRow: {
    alignItems: 'center',
    borderColor: palette.line,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 5,
    padding: 11,
  },
  conversationAvatar: {
    alignItems: 'center',
    backgroundColor: palette.primarySoft,
    borderRadius: 8,
    height: 44,
    justifyContent: 'center',
    marginRight: 8,
    width: 44,
  },
  conversationAvatarText: {
    color: palette.primaryStrong,
    fontWeight: '900',
  },
  conversationMeta: {
    color: palette.primaryStrong,
    fontSize: 11,
    fontWeight: '800',
    marginTop: 3,
  },
  badge: {
    alignSelf: 'center',
    backgroundColor: palette.primary,
    borderRadius: 999,
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '900',
    marginTop: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  chatPage: {
    gap: 12,
  },
  chatHeader: {
    alignItems: 'center',
    backgroundColor: palette.surface,
    borderColor: palette.line,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 12,
    padding: 12,
  },
  backButton: {
    alignItems: 'center',
    backgroundColor: palette.primarySoft,
    borderRadius: 8,
    paddingHorizontal: 13,
    paddingVertical: 10,
  },
  backButtonText: {
    color: palette.primaryStrong,
    fontWeight: '900',
  },
  chatBody: {
    backgroundColor: palette.surface,
    borderColor: palette.line,
    borderRadius: 8,
    borderWidth: 1,
    gap: 10,
    minHeight: 420,
    padding: 12,
  },
  messageRow: {
    alignItems: 'flex-start',
    width: '100%',
  },
  myMessageRow: {
    alignItems: 'flex-end',
  },
  bubble: {
    backgroundColor: palette.surfaceSoft,
    borderRadius: 8,
    maxWidth: '86%',
    padding: 11,
  },
  myBubble: {
    backgroundColor: palette.primary,
  },
  bubbleText: {
    color: palette.text,
  },
  myBubbleText: {
    color: '#FFFFFF',
  },
  bubbleTime: {
    color: palette.muted,
    fontSize: 10,
    marginTop: 5,
  },
  myBubbleTime: {
    color: '#DFF5EE',
    fontSize: 10,
    marginTop: 5,
  },
  composer: {
    alignItems: 'center',
    backgroundColor: palette.surface,
    borderColor: palette.line,
    borderRadius: 8,
    borderWidth: 1,
    flexDirection: 'row',
    gap: 10,
    padding: 10,
  },
  composerInput: {
    backgroundColor: palette.surfaceSoft,
    borderRadius: 8,
    color: palette.text,
    flex: 1,
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  sendButton: {
    backgroundColor: palette.primary,
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 11,
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontWeight: '900',
  },
  profilePhotoRow: {
    alignItems: 'center',
    backgroundColor: palette.surfaceSoft,
    borderRadius: 8,
    flexDirection: 'row',
    gap: 14,
    padding: 12,
  },
  ticket: {
    borderColor: palette.line,
    borderRadius: 8,
    borderWidth: 1,
    gap: 6,
    padding: 12,
  },
  note: {
    backgroundColor: palette.surfaceSoft,
    borderRadius: 8,
    color: palette.primaryStrong,
    fontSize: 12,
    fontWeight: '800',
    padding: 8,
  },
  empty: {
    alignItems: 'center',
    borderColor: palette.line,
    borderRadius: 8,
    borderStyle: 'dashed',
    borderWidth: 1,
    gap: 6,
    padding: 18,
  },
  emptyTitle: {
    color: palette.text,
    fontWeight: '900',
  },
  avatar: {
    borderRadius: 8,
  },
  avatarFallback: {
    alignItems: 'center',
    backgroundColor: palette.primarySoft,
    borderColor: palette.line,
    borderWidth: 1,
    justifyContent: 'center',
  },
  avatarText: {
    color: palette.primaryStrong,
    fontWeight: '900',
  },
  tabbar: {
    backgroundColor: palette.surface,
    borderTopColor: palette.line,
    borderTopWidth: 1,
    bottom: 0,
    flexDirection: 'row',
    left: 0,
    paddingBottom: 8,
    paddingTop: 8,
    position: 'absolute',
    right: 0,
  },
  tabButton: {
    alignItems: 'center',
    flex: 1,
    gap: 2,
  },
  tabIcon: {
    color: palette.muted,
    fontSize: 17,
    fontWeight: '900',
  },
  tabText: {
    color: palette.muted,
    fontSize: 10,
    fontWeight: '900',
  },
  tabActive: {
    color: palette.primaryStrong,
  },
});
