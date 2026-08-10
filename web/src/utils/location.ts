import type { Booking, Coordinates } from '../types';

export function requestBrowserLocation(): Promise<Coordinates> {
  if (typeof window === 'undefined' || !('geolocation' in navigator)) {
    return Promise.reject(new Error('Geolocation is not supported by your browser.'));
  }

  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const coords = {
          latitude: parseFloat(position.coords.latitude.toFixed(6)),
          longitude: parseFloat(position.coords.longitude.toFixed(6)),
        };
        resolve(coords);
      },
      (error) => {
        switch (error.code) {
          case error.PERMISSION_DENIED:
            reject(new Error('Location permission was denied.'));
            break;
          case error.POSITION_UNAVAILABLE:
            reject(new Error('Location information is unavailable.'));
            break;
          case error.TIMEOUT:
            reject(new Error('Location request timed out.'));
            break;
          default:
            reject(new Error('Could not get your location.'));
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 },
    );
  });
}

export function openDirectionsForBooking(booking: Booking, userCoordinates?: Coordinates | null) {
  if (booking.service_latitude == null || booking.service_longitude == null) {
    alert('This booking does not have a saved service location.');
    return;
  }

  const destLat = Number(booking.service_latitude);
  const destLng = Number(booking.service_longitude);

  if (!Number.isFinite(destLat) || !Number.isFinite(destLng)) {
    alert('Invalid service coordinates.');
    return;
  }

  let url = `https://www.google.com/maps/dir/?api=1&destination=${destLat},${destLng}`;
  if (userCoordinates && Number.isFinite(userCoordinates.latitude) && Number.isFinite(userCoordinates.longitude)) {
    url += `&origin=${userCoordinates.latitude},${userCoordinates.longitude}`;
  }

  window.open(url, '_blank', 'noopener,noreferrer');
}
