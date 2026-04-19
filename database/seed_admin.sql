-- Insert admin user (password: admin123)
-- Password hash generated using passlib bcrypt
INSERT INTO admins (email, password_hash, name, is_active)
VALUES (
  'admin@localift.com',
  '$2b$12$5Mw.8GJG9K8QCXhQK9h8zO0XFQN3K9QCXhQK9h8z.K5F5F5F5F5F5F5', -- This is a placeholder, needs to be generated
  'Admin User',
  true
);
