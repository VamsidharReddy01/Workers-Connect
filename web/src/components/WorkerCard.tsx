import type { WorkerProfile } from '../types';
import { RatingStars } from './RatingStars';

interface WorkerCardProps {
  worker: WorkerProfile;
  isSelected: boolean;
  onSelect: (worker: WorkerProfile) => void;
}

export function WorkerCard({ worker, isSelected, onSelect }: WorkerCardProps) {
  const initials = worker.user.username.slice(0, 2).toUpperCase();

  return (
    <div
      className={`worker-card ${isSelected ? 'selected' : ''}`}
      onClick={() => onSelect(worker)}
    >
      <div className="worker-card-main">
        {worker.user.profile_photo_url ? (
          <img
            src={worker.user.profile_photo_url}
            alt={worker.user.username}
            className="avatar-img"
          />
        ) : (
          <div className="avatar-placeholder">{initials}</div>
        )}
        <div className="worker-info">
          <div className="worker-header">
            <h4>{worker.user.username}</h4>
            <span className="badge-online">
              {worker.is_online ? '● Online' : '○ Offline'}
            </span>
          </div>
          <p className="worker-category">{worker.category}</p>
          <div className="worker-metrics">
            <span className="rating">
              <RatingStars rating={worker.rating} /> {worker.rating} ({worker.total_reviews})
            </span>
            {worker.distance_km != null && (
              <span className="distance-badge">
                📍 {worker.distance_km} km away
              </span>
            )}
          </div>
        </div>
      </div>
      <div className="worker-price-tag">
        <span className="exp">{worker.experience_years}+ yrs</span>
        <span className="price">${worker.price}</span>
      </div>
    </div>
  );
}
