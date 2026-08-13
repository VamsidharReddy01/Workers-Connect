/**
 * WorkersBridge — Mobile Notification Service
 *
 * Handles the complete FCM push notification lifecycle:
 *  - Permission request (called post-login, not on cold start)
 *  - FCM token registration with the backend
 *  - FCM token deregistration on logout
 *  - Foreground notification display
 *  - Background / cold-start notification payload parsing
 *  - Deep-link routing from notification data
 *
 * Architecture:
 *   expo-notifications
 *       ↓
 *   NotificationService (this file)
 *       ↓
 *   Backend /api/notifications/device-token/
 *       ↓
 *   routeNotification() → setScreen / setBookingId
 */

import { Platform } from 'react-native';
import * as Notifications from 'expo-notifications';
import { api } from './api';
import type { NotificationType } from './types';

// ── Configure foreground notification behaviour ───────────────────────────────
// Show the notification as a banner even when the app is in the foreground.
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

// ── Types ─────────────────────────────────────────────────────────────────────

export type NotificationData = {
  notification_type?: NotificationType;
  booking_id?: string;
  conversation_id?: string;
  [key: string]: string | undefined;
};

export type NavigationTarget =
  | { screen: 'workerBookingDetail'; bookingId: number }
  | { screen: 'customerBookingDetail'; bookingId: number }
  | { screen: 'messages'; conversationId?: number }
  | { screen: 'notifications' }
  | null;

// ── Android notification channels ─────────────────────────────────────────────

async function ensureAndroidChannels() {
  if (Platform.OS !== 'android') return;

  await Notifications.setNotificationChannelAsync('job_updates', {
    name: 'Job Updates',
    importance: Notifications.AndroidImportance.HIGH,
    vibrationPattern: [0, 250, 250, 250],
    lightColor: '#007F68',
    sound: 'default',
  });

  await Notifications.setNotificationChannelAsync('messages', {
    name: 'Messages',
    importance: Notifications.AndroidImportance.HIGH,
    vibrationPattern: [0, 150],
    lightColor: '#007F68',
    sound: 'default',
  });

  await Notifications.setNotificationChannelAsync('system', {
    name: 'System Notifications',
    importance: Notifications.AndroidImportance.DEFAULT,
  });
}

// ── Permission request ────────────────────────────────────────────────────────

/**
 * Request notification permission.
 * Should be called after login (not on app cold start without context).
 * Returns true if permission was granted.
 */
export async function requestNotificationPermission(): Promise<boolean> {
  await ensureAndroidChannels();

  const { status: existing } = await Notifications.getPermissionsAsync();
  if (existing === 'granted') return true;

  const { status } = await Notifications.requestPermissionsAsync();
  return status === 'granted';
}

// ── FCM Token registration ────────────────────────────────────────────────────

/**
 * Get the Expo / FCM push token and register it with the WorkersBridge backend.
 * Silently fails if permission not granted or network error.
 */
export async function registerPushToken(accessToken: string): Promise<string | null> {
  try {
    const granted = await requestNotificationPermission();
    if (!granted) return null;

    // Get the Expo push token (which wraps FCM on Android, APNs on iOS)
    const tokenData = await Notifications.getExpoPushTokenAsync({
      projectId: 'worker-s-bridge', // matches Firebase project ID
    });
    const pushToken = tokenData.data;
    const platform = Platform.OS === 'ios' ? 'ios' : 'android';

    await api.registerDeviceToken(accessToken, pushToken, platform);
    return pushToken;
  } catch (error) {
    console.warn('[NotificationService] Could not register push token:', error);
    return null;
  }
}

/**
 * Deregister the push token on logout.
 * Called before clearing the access token from storage.
 */
export async function deregisterPushToken(accessToken: string): Promise<void> {
  try {
    const tokenData = await Notifications.getExpoPushTokenAsync({
      projectId: 'worker-s-bridge',
    }).catch(() => null);

    const pushToken = tokenData?.data;
    await api.deregisterDeviceToken(accessToken, pushToken);
  } catch {
    // Best-effort; swallow errors
  }
}

// ── Notification routing ──────────────────────────────────────────────────────

/**
 * Maps a notification data payload to a navigation target.
 * Used for foreground taps, background taps, and cold-start handling.
 */
export function resolveNavigationTarget(
  data: NotificationData,
  userRole: 'customer' | 'worker' | 'admin',
): NavigationTarget {
  const type = data.notification_type;
  const bookingId = data.booking_id ? parseInt(data.booking_id, 10) : null;
  const conversationId = data.conversation_id ? parseInt(data.conversation_id, 10) : undefined;

  if (!type) return null;

  switch (type) {
    case 'JOB_REQUEST_RECEIVED':
      // Worker receives a new request
      if (bookingId) return { screen: 'workerBookingDetail', bookingId };
      return { screen: 'notifications' };

    case 'JOB_ACCEPTED':
    case 'JOB_DECLINED':
    case 'WORKER_ON_THE_WAY':
    case 'JOB_STARTED':
    case 'JOB_COMPLETED':
      // Customer receives job lifecycle updates
      if (bookingId) return { screen: 'customerBookingDetail', bookingId };
      return { screen: 'notifications' };

    case 'JOB_CANCELLED':
      if (bookingId) {
        const screen =
          userRole === 'worker' ? 'workerBookingDetail' : 'customerBookingDetail';
        return { screen, bookingId };
      }
      return { screen: 'notifications' };

    case 'NEW_MESSAGE':
      return { screen: 'messages', conversationId };

    default:
      return { screen: 'notifications' };
  }
}

/**
 * Extract notification data from an Expo notification response.
 */
export function extractNotificationData(
  response: Notifications.NotificationResponse,
): NotificationData {
  const payload = response.notification.request.content.data as NotificationData;
  return payload ?? {};
}

/**
 * Check if there is a pending notification response from when the app was
 * launched via a push notification tap (cold start).
 * Returns the navigation target if one exists, otherwise null.
 */
export async function getPendingNotificationTarget(
  userRole: 'customer' | 'worker' | 'admin',
): Promise<NavigationTarget> {
  try {
    const response = await Notifications.getLastNotificationResponseAsync();
    if (!response) return null;
    const data = extractNotificationData(response);
    return resolveNavigationTarget(data, userRole);
  } catch {
    return null;
  }
}
