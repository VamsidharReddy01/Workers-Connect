export type UserRole = 'customer' | 'worker' | 'admin';

export type User = {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  phone_number?: string | null;
  location?: string | null;
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
  phone_number?: string;
  location?: string;
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
  category: string;
  price: string;
  bio: string;
  is_online: boolean;
  rating: number;
  total_reviews: number;
  experience_years: number;
  cover_image_url: string | null;
  work_images: WorkerImage[];
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
