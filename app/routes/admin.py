from datetime import datetime

import secrets
import string
from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user
from sqlalchemy import func

from app.extensions import bcrypt, db
from app.models.admin_log import AdminLog
from app.models.booking import Booking
from app.models.helper import Helper
from app.models.helper_application import HelperApplication
from app.models.notification import Notification
from app.models.review import Review
from app.models.user import User


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(func):
    @wraps(func)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return func(*args, **kwargs)

    return wrapper


def _generate_helper_login_id() -> str:
    latest = Helper.query.order_by(Helper.id.desc()).first()
    next_id = (latest.id + 1) if latest else 1001
    return f"HL-{next_id}"


def _generate_temp_password(length: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#%"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _log_admin_action(action: str, entity_type: str | None = None, entity_id: str | None = None, details: str | None = None) -> None:
    db.session.add(AdminLog(admin_id=current_user.id, action=action, entity_type=entity_type, entity_id=entity_id, details=details))


def _notify(user_id: int, title: str, message: str, category: str = "info") -> None:
    db.session.add(Notification(user_id=user_id, title=title, message=message, category=category))


@admin_bp.route("/login-side", methods=["POST"])
def admin_login_side():
    username = (request.form.get("username") or "").strip().lower()
    password = request.form.get("password") or ""

    user = User.query.filter(User.role == "admin", User.email.in_([username, "admin", "admin@localift.com"])).first()
    if user and user.check_password(password):
        login_user(user)
        user.last_login_at = datetime.utcnow()
        db.session.commit()
        flash("Admin login successful.", "success")
        return redirect(url_for("admin.dashboard"))

    flash("Invalid admin credentials.", "error")
    return redirect(url_for("auth.home"))


@admin_bp.route("")
@admin_bp.route("/")
@admin_required
def dashboard():
    users_total = User.query.filter(User.role == "customer").count() + User.query.filter(User.role == "helper").count()
    helper_total = Helper.query.filter(Helper.status != "deleted").count()
    pending_requests = HelperApplication.query.filter_by(status="pending").count()
    active_jobs = Booking.query.filter(Booking.status.in_(["pending", "accepted"])).count()
    completed_jobs = Booking.query.filter_by(status="completed").count()
    revenue = db.session.query(func.coalesce(func.sum(Booking.payment_amount), 0)).filter(Booking.status == "completed").scalar() or 0

    applications = (
        HelperApplication.query.filter(HelperApplication.status.in_(["pending", "approved"]))
        .order_by(HelperApplication.created_at.desc())
        .limit(20)
        .all()
    )
    helpers = Helper.query.order_by(Helper.average_rating.desc(), Helper.completed_jobs.desc()).limit(10).all()
    customers = User.query.filter_by(role="customer").order_by(User.created_at.desc()).limit(10).all()
    reviews = Review.query.order_by(Review.created_at.desc()).limit(8).all()

    stats = {
        "users_total": users_total,
        "helper_total": helper_total,
        "pending_requests": pending_requests,
        "active_jobs": active_jobs,
        "completed_jobs": completed_jobs,
        "revenue": float(revenue or 0),
    }
    return render_template("admin_dashboard.html", stats=stats, applications=applications, helpers=helpers, customers=customers, reviews=reviews)


@admin_bp.route("/helper/<int:application_id>")
@admin_required
def helper_details(application_id: int):
    application = HelperApplication.query.get_or_404(application_id)
    helper = Helper.query.filter_by(application_id=application.id).first()
    helper_bookings = Booking.query.filter_by(helper_id=helper.id).order_by(Booking.created_at.desc()).all() if helper else []
    customer_count = User.query.filter_by(role="customer").count()
    reviews = Review.query.filter_by(helper_id=helper.id).order_by(Review.created_at.desc()).all() if helper else []
    return render_template("admin_helper_detail.html", application=application, helper=helper, bookings=helper_bookings, reviews=reviews, customer_count=customer_count)


@admin_bp.route("/approve/<int:application_id>", methods=["POST"])
@admin_required
def approve_helper(application_id: int):
    application = HelperApplication.query.get_or_404(application_id)
    if application.status != "pending":
        flash("Application already processed.", "warning")
        return redirect(url_for("admin.dashboard"))

    user = User.query.get(application.user_id) if application.user_id else None
    temp_password = _generate_temp_password()
    if not user:
        user = User(
            full_name=application.full_name,
            email=application.email,
            phone=application.mobile_number,
            address=application.address,
            role="helper",
        )
        db.session.add(user)
        db.session.flush()
    login_id = _generate_helper_login_id()

    user.full_name = application.full_name
    user.email = application.email
    user.phone = application.mobile_number
    user.address = application.address
    user.role = "helper"
    user.is_active = True

    user.set_password(temp_password)

    helper = Helper(
        user_id=user.id,
        application_id=application.id,
        login_id=login_id,
        full_name=application.full_name,
        email=application.email,
        mobile_number=application.mobile_number,
        address=application.address,
        city=application.city,
        state=application.state,
        pincode=application.pincode,
        aadhaar_number=application.aadhaar_number,
        skill_category=application.skill_category,
        experience=application.experience,
        available_time=application.available_time,
        short_bio=application.short_bio,
        profile_photo=application.profile_photo,
        id_proof=application.id_proof,
        password_hash=user.password_hash,
        hourly_rate={"Electrician": 499, "Cleaner": 349, "Chef": 549, "Mechanic": 599, "Designer": 449, "Painter": 379, "Plumber": 469, "Carpenter": 489}.get(application.skill_category, 399),
        status="active",
        availability_on=True,
    )

    application.status = "approved"
    application.rejection_reason = None
    application.login_id = login_id
    application.temp_password = temp_password
    application.reviewed_by = current_user.id
    application.reviewed_at = datetime.utcnow()

    db.session.add(helper)
    _notify(user.id, "Helper application approved", f"Your helper login ID is {login_id}.", "success")
    _log_admin_action("approve_helper", "helper_application", str(application.id), f"Approved helper login {login_id}")
    db.session.commit()

    flash(f"Approved {application.full_name}. Login ID: {login_id} | Password: {temp_password}", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/reject/<int:application_id>", methods=["POST"])
@admin_required
def reject_helper(application_id: int):
    application = HelperApplication.query.get_or_404(application_id)
    reason = (request.form.get("reason") or "").strip()
    if not reason:
        flash("Rejection reason is required.", "error")
        return redirect(url_for("admin.dashboard"))

    application.status = "rejected"
    application.rejection_reason = reason
    application.reviewed_by = current_user.id
    application.reviewed_at = datetime.utcnow()

    if application.user_id:
        _notify(application.user_id, "Helper application update", "Sorry, you are currently not eligible. Please try again later.", "warning")

    _log_admin_action("reject_helper", "helper_application", str(application.id), reason)
    db.session.commit()
    flash("Application rejected.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/helpers/<int:helper_id>/suspend", methods=["POST"])
@admin_required
def suspend_helper(helper_id: int):
    helper = Helper.query.get_or_404(helper_id)
    helper.status = "suspended"
    helper.user.is_active = False
    _log_admin_action("suspend_helper", "helper", str(helper.id), helper.full_name)
    db.session.commit()
    flash("Helper suspended.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/helpers/<int:helper_id>/unsuspend", methods=["POST"])
@admin_required
def unsuspend_helper(helper_id: int):
    helper = Helper.query.get_or_404(helper_id)
    helper.status = "active"
    helper.user.is_active = True
    _log_admin_action("unsuspend_helper", "helper", str(helper.id), helper.full_name)
    db.session.commit()
    flash("Helper unsuspended.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/helpers/<int:helper_id>/delete", methods=["POST"])
@admin_required
def delete_helper(helper_id: int):
    helper = Helper.query.get_or_404(helper_id)
    helper.status = "deleted"
    helper.availability_on = False
    helper.user.is_active = False
    _log_admin_action("delete_helper", "helper", str(helper.id), helper.full_name)
    db.session.commit()
    flash("Helper removed.", "success")
    return redirect(url_for("admin.dashboard"))
