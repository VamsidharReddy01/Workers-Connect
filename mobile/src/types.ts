export type UserRole = 'customer' | 'worker' | 'admin';

export type User = {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  phone_number?: string | null;
  location?: string | null;
  latitude?: string | null;
  longitude?: string | null;
  location_permission_granted?: boolean;
  location_updated_at?: string | null;
  location_source?: string | null;
  profile_photo_url?: string | null;
};

export type AuthResponse = {
  access: string;
  refresh: string;
  user: User;
};

export type SignupPayload = {
  username: string;
  email: string;
  password: string;
  role: Exclude<UserRole, 'admin'>;
  category?: string;
  phone_number?: string;
  location?: string;
  latitude?: number | string | null;
  longitude?: number | string | null;
  location_permission_granted?: boolean;
  location_source?: string;
  email_otp: string;
};

export type SupportTicket = {
  id: number;
  subject: string;
  message: string;
  status: string;
  status_display: string;
  admin_note: string;
  created_at: string;
  updated_at: string;
};

export type CategorySummary = {
  category: string;
  worker_count: number;
  online_worker_count: number;
};

export type WorkerImage = {
  id: number;
  image_url: string | null;
  caption: string;
  sort_order: number;
  created_at: string;
};

export type WorkerProfile = {
  id: number;
  user: User;
  name?: string;
  category: string;
  price: string;
  bio: string;
  is_online: boolean;
  rating: number;
  total_reviews: number;
  experience_years: number;
  cover_image_url: string | null;
  work_images: WorkerImage[];
  latitude?: number | string | null;
  longitude?: number | string | null;
  location_name?: string | null;
  distance_km?: number | null;
};

export type BookingStatus =
  | 'requested'
  | 'accepted'
  | 'declined'
  | 'on_the_way'
  | 'in_progress'
  | 'completed'
  | 'cancelled';

export type Booking = {
  id: number;
  customer: User;
  worker: WorkerProfile;
  service_category: string;
  description: string;
  address: string;
  service_latitude?: string | null;
  service_longitude?: string | null;
  location_permission_granted?: boolean;
  service_location_source?: 'saved' | 'gps' | 'manual' | null;
  scheduled_at: string;
  total_amount: string;
  status: BookingStatus;
  status_display: string;
  has_review: boolean;
  conversation_id: number | null;
  created_at: string;
  updated_at: string;
};

export type WorkerMetrics = {
  pending_requests: number;
  active_jobs: number;
  completed_jobs: number;
  total_earnings: string;
};

export type WorkerDashboardSummary = {
  profile: WorkerProfile;
  metrics: WorkerMetrics;
};

export type Message = {
  id: number;
  sender: User;
  text: string;
  created_at: string;
  is_read: boolean;
};

export type Conversation = {
  id: number;
  booking: Booking;
  last_message: Message | null;
  unread_count: number;
  other_party_name: string;
  created_at: string;
  updated_at: string;
};

export type Coordinates = {
  latitude: number;
  longitude: number;
};

export type NotificationType =
  | 'JOB_REQUEST_RECEIVED'
  | 'JOB_ACCEPTED'
  | 'JOB_DECLINED'
  | 'WORKER_ON_THE_WAY'
  | 'JOB_STARTED'
  | 'JOB_COMPLETED'
  | 'JOB_CANCELLED'
  | 'NEW_MESSAGE'
  | 'SYSTEM_NOTIFICATION';

export type AppNotification = {
  id: number;
  notification_type: NotificationType;
  title: string;
  message: string;
  related_booking_id: number | null;
  data: Record<string, string>;
  is_read: boolean;
  created_at: string;
};
