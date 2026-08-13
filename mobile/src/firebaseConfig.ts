// Firebase configuration for Workers Bridge app
// Uses the Firebase Web SDK which works with Expo (no native build required)
// For native Android features (FCM push notifications etc.), EAS Build will use google-services.json

import { initializeApp, getApps, getApp } from 'firebase/app';

const firebaseConfig = {
  apiKey: 'AIzaSyBR3btkASoVk2ZwD-mBnfB1Mism91pr4JY',
  projectId: 'worker-s-bridge',
  storageBucket: 'worker-s-bridge.firebasestorage.app',
  appId: '1:533693893514:android:8010a0bb479e0c4fe71673',
  messagingSenderId: '533693893514',
};

// Initialize Firebase (guard against hot-reload re-initialization)
const app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();

export default app;
