INSERT INTO users (full_name, email, phone, password_hash, role, is_verified) VALUES
('Anita Sharma', 'anita.user@localift.com', '9990001001', '$2b$12$KIXF6zjK2m5xVFb6b0JSTe4hgbf28pQx3knf6Zs1q4N4qzQ9V6QFy', 'user', TRUE),
('Rahul Plumber', 'rahul.plumber@localift.com', '9990001002', '$2b$12$KIXF6zjK2m5xVFb6b0JSTe4hgbf28pQx3knf6Zs1q4N4qzQ9V6QFy', 'helper', TRUE),
('Neha Tutor', 'neha.tutor@localift.com', '9990001003', '$2b$12$KIXF6zjK2m5xVFb6b0JSTe4hgbf28pQx3knf6Zs1q4N4qzQ9V6QFy', 'helper', TRUE),
('Imran Electrician', 'imran.electric@localift.com', '9990001004', '$2b$12$KIXF6zjK2m5xVFb6b0JSTe4hgbf28pQx3knf6Zs1q4N4qzQ9V6QFy', 'helper', TRUE)
ON CONFLICT (email) DO NOTHING;

INSERT INTO helpers (user_id, category, bio, city, latitude, longitude, hourly_rate, avg_rating, completed_jobs, response_time_minutes, availability, trust_score, profile_photo) VALUES
(2, 'Plumber', 'Leak fixes and emergency plumbing', 'Mumbai', 19.0760, 72.8777, 550, 4.7, 132, 20, TRUE, 92, 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300'),
(3, 'Tutor', 'Math and science tutor for grades 6-12', 'Mumbai', 19.0820, 72.8810, 700, 4.8, 95, 35, TRUE, 90, 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=300'),
(4, 'Electrician', 'Wiring, switchboards, and quick repairs', 'Mumbai', 19.0700, 72.8700, 650, 4.5, 110, 28, TRUE, 88, 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=300')
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO services (helper_id, title, description, base_price) VALUES
(1, 'Emergency Pipe Repair', 'Fix burst or leaking pipes', 500),
(2, '1 Hour Tutoring Session', 'Personalized one-on-one tutoring', 700),
(3, 'Home Electrical Check', 'Safety and wiring inspection', 600)
ON CONFLICT DO NOTHING;
