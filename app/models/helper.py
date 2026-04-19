from datetime import datetime

from app.extensions import db


class Helper(db.Model):
    __tablename__ = "helpers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    application_id = db.Column(db.Integer, db.ForeignKey("helper_applications.id"), nullable=True, unique=True)
    login_id = db.Column(db.String(40), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(140), nullable=False)
    email = db.Column(db.String(140), nullable=False, index=True)
    mobile_number = db.Column(db.String(20), nullable=False)
    address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    pincode = db.Column(db.String(12), nullable=False)
    aadhaar_number = db.Column(db.String(20), nullable=False)
    skill_category = db.Column(db.String(80), nullable=False, index=True)
    experience = db.Column(db.Integer, nullable=False, default=0)
    available_time = db.Column(db.String(120), nullable=False)
    short_bio = db.Column(db.Text, nullable=False)
    profile_photo = db.Column(db.String(255), nullable=True)
    id_proof = db.Column(db.String(255), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default="active", nullable=False, index=True)
    availability_on = db.Column(db.Boolean, default=True, nullable=False)
    hourly_rate = db.Column(db.Float, default=0.0, nullable=False)
    total_earnings = db.Column(db.Float, default=0.0, nullable=False)
    average_rating = db.Column(db.Float, default=0.0, nullable=False)
    total_jobs = db.Column(db.Integer, default=0, nullable=False)
    completed_jobs = db.Column(db.Integer, default=0, nullable=False)
    pending_jobs = db.Column(db.Integer, default=0, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="helper_profile", foreign_keys=[user_id])
    application = db.relationship("HelperApplication", back_populates="helper_profile", foreign_keys=[application_id], uselist=False)
    bookings = db.relationship("Booking", back_populates="helper", cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="helper", cascade="all, delete-orphan")

    def recompute_metrics(self) -> None:
        completed = sum(1 for booking in self.bookings if booking.status == "completed")
        pending = sum(1 for booking in self.bookings if booking.status in {"pending", "accepted"})
        revenue = sum(float(booking.payment_amount or 0) for booking in self.bookings if booking.status == "completed")
        ratings = [review.rating for review in self.reviews]

        self.total_jobs = len(self.bookings)
        self.completed_jobs = completed
        self.pending_jobs = pending
        self.total_earnings = round(revenue, 2)
        self.average_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0.0
