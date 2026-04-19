from datetime import datetime

from flask_login import UserMixin

from app.extensions import bcrypt, db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(140), nullable=False)
    email = db.Column(db.String(140), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="customer", nullable=False, index=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    helper_application = db.relationship(
        "HelperApplication",
        back_populates="user",
        uselist=False,
        foreign_keys="HelperApplication.user_id",
    )
    helper_profile = db.relationship("Helper", back_populates="user", uselist=False)
    bookings = db.relationship("Booking", back_populates="customer", foreign_keys="Booking.customer_id")
    notifications = db.relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    admin_logs = db.relationship("AdminLog", back_populates="admin", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))
