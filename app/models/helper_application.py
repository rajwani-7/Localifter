from datetime import datetime

from app.extensions import db


class HelperApplication(db.Model):
    __tablename__ = "helper_applications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, index=True)
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
    status = db.Column(db.String(20), default="pending", nullable=False, index=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    login_id = db.Column(db.String(40), nullable=True)
    temp_password = db.Column(db.String(255), nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="helper_application", foreign_keys=[user_id])
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])
    helper_profile = db.relationship("Helper", back_populates="application", uselist=False, foreign_keys="Helper.application_id")
