from datetime import datetime

from app.extensions import db


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    helper_id = db.Column(db.Integer, db.ForeignKey("helpers.id"), nullable=False, index=True)
    service_category = db.Column(db.String(80), nullable=False)
    customer_name = db.Column(db.String(140), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    scheduled_at = db.Column(db.DateTime, nullable=False)
    payment_amount = db.Column(db.Float, default=0.0, nullable=False)
    payment_status = db.Column(db.String(20), default="unpaid", nullable=False)
    status = db.Column(db.String(20), default="pending", nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customer = db.relationship("User", back_populates="bookings", foreign_keys=[customer_id])
    helper = db.relationship("Helper", back_populates="bookings")
    review = db.relationship("Review", back_populates="booking", uselist=False)
