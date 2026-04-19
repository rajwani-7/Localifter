import secrets
from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, or_

from app.extensions import db
from app.forms.auth_forms import HelperApplicationForm
from app.models.booking import Booking
from app.models.helper import Helper
from app.models.helper_application import HelperApplication
from app.models.notification import Notification
from app.models.review import Review
from app.models.user import User
from app.utils.uploads import save_upload


helper_bp = Blueprint("helper", __name__)

SERVICE_RATE = {
    "Electrician": 499,
    "Cleaner": 349,
    "Chef": 549,
    "Mechanic": 599,
    "Designer": 449,
    "Painter": 379,
    "Plumber": 469,
    "Carpenter": 489,
}


def _require_customer():
    if not current_user.is_authenticated or current_user.role != "customer":
        flash("Please log in as a customer to continue.", "error")
        return False
    return True


def _require_helper():
    if not current_user.is_authenticated or current_user.role != "helper":
        flash("Please log in as a helper to continue.", "error")
        return False
    if not current_user.helper_profile or current_user.helper_profile.status != "active":
        flash("Your helper account is not active.", "error")
        return False
    return True


def _helper_query():
    return Helper.query.filter(Helper.status == "active", Helper.availability_on.is_(True))


def _notify(user_id: int, title: str, message: str, category: str = "info") -> None:
    db.session.add(Notification(user_id=user_id, title=title, message=message, category=category))


@helper_bp.route("/want-helper")
def want_helper():
    return render_template("want_helper.html")


@helper_bp.route("/become-helper", methods=["GET", "POST"])
def become_helper():
    form = HelperApplicationForm()

    if current_user.is_authenticated and current_user.role == "helper" and current_user.helper_profile:
        return redirect(url_for("helper.helper_dashboard"))

    if form.validate_on_submit():
        applicant_user = None
        submitted_email = form.email.data.strip().lower()

        # Use logged-in customer account directly; otherwise resolve by submitted email.
        if current_user.is_authenticated and current_user.role == "customer":
            applicant_user = current_user
            email = (current_user.email or submitted_email).strip().lower()
        else:
            email = submitted_email
            applicant_user = User.query.filter_by(email=email).first()

        if applicant_user and applicant_user.role == "helper" and applicant_user.helper_profile:
            flash("This account is already a helper account.", "warning")
            return redirect(url_for("auth.login"))

        if not applicant_user:
            applicant_user = User(
                full_name=form.full_name.data.strip(),
                email=email,
                phone=form.mobile_number.data.strip(),
                address=form.address.data.strip(),
                role="customer",
            )
            applicant_user.set_password(secrets.token_urlsafe(16))
            db.session.add(applicant_user)
            db.session.flush()
        else:
            # Sync key profile details from latest application draft.
            applicant_user.full_name = form.full_name.data.strip()
            applicant_user.phone = form.mobile_number.data.strip()
            applicant_user.address = form.address.data.strip()
            if not applicant_user.email:
                applicant_user.email = email

        already_applied = HelperApplication.query.filter(
            HelperApplication.user_id == applicant_user.id,
            HelperApplication.status.in_(["pending", "approved"]),
        ).first()
        if already_applied:
            flash("An application already exists for this email.", "warning")
            return redirect(url_for("helper.helper_status"))

        try:
            profile_photo = save_upload(form.profile_photo.data, "profile_photos")
            id_proof = save_upload(form.id_proof.data, "government_ids")
        except ValueError as exc:
            flash(str(exc), "error")
            return render_template("become_helper.html", form=form), 400

        application = HelperApplication(
            user_id=applicant_user.id,
            full_name=form.full_name.data.strip(),
            email=email,
            mobile_number=form.mobile_number.data.strip(),
            address=form.address.data.strip(),
            city=form.city.data.strip(),
            state=form.state.data.strip(),
            pincode=form.pincode.data.strip(),
            aadhaar_number=form.aadhaar_number.data.strip(),
            skill_category=form.skill_category.data,
            experience=int(form.experience.data),
            available_time=form.available_time.data.strip(),
            short_bio=form.short_bio.data.strip(),
            profile_photo=profile_photo,
            id_proof=id_proof,
            status="pending",
        )
        db.session.add(application)
        _notify(applicant_user.id, "Helper application received", "Your helper application is under review.", "success")

        # Notify all admins that a new helper application is waiting for review.
        admin_users = User.query.filter_by(role="admin").all()
        for admin_user in admin_users:
            _notify(
                admin_user.id,
                "New helper application",
                f"{application.full_name} submitted a helper application.",
                "info",
            )
        db.session.commit()

        if current_user.is_authenticated and current_user.id != applicant_user.id:
            logout_user()
        if not current_user.is_authenticated or current_user.id != applicant_user.id:
            login_user(applicant_user)

        flash("Application submitted. Your request is under admin review.", "success")
        return redirect(url_for("helper.helper_status", just_submitted=1))

    if request.method == "POST":
        flash("Please correct the form errors and try again.", "error")

    return render_template("become_helper.html", form=form)


@helper_bp.route("/helper/application/status")
@login_required
def helper_status():
    application = HelperApplication.query.filter_by(user_id=current_user.id).order_by(HelperApplication.created_at.desc()).first()
    just_submitted = request.args.get("just_submitted") == "1"
    return render_template("helper_status.html", application=application, just_submitted=just_submitted)


@helper_bp.route("/dashboard")
@login_required
def customer_dashboard():
    if not _require_customer():
        return redirect(url_for("auth.login"))

    category = request.args.get("category", "")
    query = request.args.get("q", "")
    helpers = _helper_query()

    if category:
        helpers = helpers.filter(Helper.skill_category == category)
    if query:
        like = f"%{query.strip().lower()}%"
        helpers = helpers.filter(
            or_(
                func.lower(Helper.full_name).like(like),
                func.lower(Helper.city).like(like),
                func.lower(Helper.short_bio).like(like),
            )
        )

    helper_list = helpers.order_by(Helper.average_rating.desc(), Helper.completed_jobs.desc()).limit(24).all()
    unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).limit(6).all()
    return render_template(
        "customer_dashboard.html",
        helpers=helper_list,
        unread_notifications=unread_notifications,
        categories=list(SERVICE_RATE.keys()),
    )


@helper_bp.route("/helpers/search")
@login_required
def search_helpers():
    if not _require_customer():
        return jsonify([]), 403

    category = request.args.get("category", "")
    query = request.args.get("q", "")
    helpers = _helper_query()

    if category:
        helpers = helpers.filter(Helper.skill_category == category)
    if query:
        like = f"%{query.strip().lower()}%"
        helpers = helpers.filter(
            or_(
                func.lower(Helper.full_name).like(like),
                func.lower(Helper.city).like(like),
                func.lower(Helper.short_bio).like(like),
            )
        )

    payload = []
    for helper in helpers.order_by(Helper.average_rating.desc(), Helper.completed_jobs.desc()).all():
        payload.append(
            {
                "id": helper.id,
                "full_name": helper.full_name,
                "skill_category": helper.skill_category,
                "experience": helper.experience,
                "average_rating": helper.average_rating,
                "completed_jobs": helper.completed_jobs,
                "hourly_rate": helper.hourly_rate,
                "availability_on": helper.availability_on,
                "city": helper.city,
                "profile_photo": helper.profile_photo,
                "short_bio": helper.short_bio,
            }
        )
    return jsonify(payload)


@helper_bp.route("/helpers/<int:helper_id>")
@login_required
def helper_profile(helper_id: int):
    if not _require_customer():
        return redirect(url_for("auth.login"))

    helper = Helper.query.get_or_404(helper_id)
    reviews = Review.query.filter_by(helper_id=helper.id).order_by(Review.created_at.desc()).limit(6).all()
    bookings = Booking.query.filter_by(helper_id=helper.id).order_by(Booking.created_at.desc()).limit(8).all()
    return render_template(
        "helper_profile.html",
        helper=helper,
        reviews=reviews,
        bookings=bookings,
        rate=SERVICE_RATE.get(helper.skill_category, 399),
    )


@helper_bp.route("/helpers/<int:helper_id>/hire", methods=["POST"])
@login_required
def hire_helper(helper_id: int):
    if not _require_customer():
        return redirect(url_for("auth.login"))

    helper = Helper.query.get_or_404(helper_id)
    scheduled_at_raw = request.form.get("scheduled_at", "")
    location = (request.form.get("location") or "").strip()
    notes = (request.form.get("notes") or "").strip()

    if not scheduled_at_raw or not location:
        flash("Select a schedule and location.", "error")
        return redirect(url_for("helper.helper_profile", helper_id=helper.id))

    scheduled_at = datetime.fromisoformat(scheduled_at_raw)
    booking = Booking(
        customer_id=current_user.id,
        helper_id=helper.id,
        service_category=helper.skill_category,
        customer_name=current_user.full_name,
        customer_phone=current_user.phone or "",
        location=location,
        scheduled_at=scheduled_at,
        payment_amount=helper.hourly_rate,
        payment_status="pending",
        status="pending",
        notes=notes,
    )
    db.session.add(booking)
    _notify(helper.user_id, "New help request", f"A customer requested {helper.skill_category} service.", "info")
    db.session.commit()
    flash("Booking request created successfully.", "success")
    return redirect(url_for("helper.helper_profile", helper_id=helper.id))


@helper_bp.route("/helpers/<int:helper_id>/rebook", methods=["POST"])
@login_required
def rebook_helper(helper_id: int):
    if not _require_customer():
        return redirect(url_for("auth.login"))

    helper = Helper.query.get_or_404(helper_id)
    latest_booking = Booking.query.filter_by(customer_id=current_user.id, helper_id=helper.id).order_by(Booking.created_at.desc()).first()
    if not latest_booking:
        flash("No previous booking found to rebook.", "warning")
        return redirect(url_for("helper.helper_profile", helper_id=helper.id))

    booking = Booking(
        customer_id=current_user.id,
        helper_id=helper.id,
        service_category=latest_booking.service_category,
        customer_name=current_user.full_name,
        customer_phone=current_user.phone or "",
        location=latest_booking.location,
        scheduled_at=datetime.utcnow(),
        payment_amount=helper.hourly_rate,
        payment_status="pending",
        status="pending",
        notes="Rebooked from previous request",
    )
    db.session.add(booking)
    _notify(helper.user_id, "Rebook request", f"{current_user.full_name} rebooked your service.", "info")
    db.session.commit()
    flash("Helper rebooked successfully.", "success")
    return redirect(url_for("helper.helper_profile", helper_id=helper.id))


@helper_bp.route("/bookings/<int:booking_id>/review", methods=["POST"])
@login_required
def leave_review(booking_id: int):
    if not _require_customer():
        return redirect(url_for("auth.login"))

    booking = Booking.query.filter_by(id=booking_id, customer_id=current_user.id).first_or_404()
    if booking.status != "completed":
        flash("You can only review completed work.", "warning")
        return redirect(url_for("helper.helper_profile", helper_id=booking.helper_id))

    rating = int(request.form.get("rating", 0))
    comment = (request.form.get("comment") or "").strip()
    review = Review(booking_id=booking.id, customer_id=current_user.id, helper_id=booking.helper_id, rating=rating, comment=comment)
    db.session.add(review)

    helper = booking.helper
    helper.recompute_metrics()
    _notify(helper.user_id, "New review received", f"You received a {rating}-star review.", "success")
    db.session.commit()
    flash("Review submitted.", "success")
    return redirect(url_for("helper.helper_profile", helper_id=helper.id))


@helper_bp.route("/helper/dashboard")
@login_required
def helper_dashboard():
    if not _require_helper():
        return redirect(url_for("helper.helper_status"))

    helper = current_user.helper_profile
    helper.recompute_metrics()
    db.session.commit()

    bookings = Booking.query.filter_by(helper_id=helper.id).order_by(Booking.created_at.desc()).all()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(8).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    reviews = Review.query.filter_by(helper_id=helper.id).order_by(Review.created_at.desc()).limit(8).all()
    stats = {
        "total_jobs": helper.total_jobs,
        "completed_jobs": helper.completed_jobs,
        "pending_jobs": helper.pending_jobs,
        "total_earnings": helper.total_earnings,
        "average_rating": helper.average_rating,
    }
    return render_template(
        "helper_dashboard.html",
        helper=helper,
        bookings=bookings,
        notifications=notifications,
        unread_count=unread_count,
        reviews=reviews,
        stats=stats,
    )


@helper_bp.route("/helper/notifications/read-all", methods=["POST"])
@login_required
def read_helper_notifications():
    if not _require_helper():
        return redirect(url_for("helper.helper_status"))

    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    flash("Notifications marked as read.", "success")
    return redirect(url_for("helper.helper_dashboard"))


@helper_bp.route("/helper/bookings/<int:booking_id>/<action>", methods=["POST"])
@login_required
def handle_booking(booking_id: int, action: str):
    if not _require_helper():
        return redirect(url_for("helper.helper_status"))

    helper = current_user.helper_profile
    booking = Booking.query.filter_by(id=booking_id, helper_id=helper.id).first_or_404()

    if action not in {"accept", "reject", "complete"}:
        flash("Invalid booking action.", "error")
        return redirect(url_for("helper.helper_dashboard"))

    if action == "accept":
        booking.status = "accepted"
        message = "Your helper request has been accepted."
    elif action == "reject":
        booking.status = "rejected"
        message = "Your helper request was rejected."
    else:
        booking.status = "completed"
        booking.payment_status = "paid"
        message = "Work has been marked as completed."

    helper.recompute_metrics()
    _notify(booking.customer_id, "Booking update", message, "success")
    db.session.commit()
    flash(f"Booking marked as {booking.status}.", "success")
    return redirect(url_for("helper.helper_dashboard"))


@helper_bp.route("/helper/availability", methods=["POST"])
@login_required
def toggle_helper_availability():
    if not _require_helper():
        return redirect(url_for("helper.helper_status"))

    helper = current_user.helper_profile
    helper.availability_on = request.form.get("availability_on") == "on"
    db.session.commit()
    flash("Availability updated.", "success")
    return redirect(url_for("helper.helper_dashboard"))


@helper_bp.route("/helper/profile", methods=["POST"])
@login_required
def update_helper_profile():
    if not _require_helper():
        return redirect(url_for("helper.helper_status"))

    helper = current_user.helper_profile
    helper.full_name = (request.form.get("full_name") or helper.full_name).strip()
    helper.mobile_number = (request.form.get("mobile_number") or helper.mobile_number).strip()
    helper.city = (request.form.get("city") or helper.city).strip()
    helper.state = (request.form.get("state") or helper.state).strip()
    helper.available_time = (request.form.get("available_time") or helper.available_time).strip()
    helper.short_bio = (request.form.get("short_bio") or helper.short_bio).strip()
    helper.hourly_rate = request.form.get("hourly_rate", type=float) or helper.hourly_rate
    helper.availability_on = request.form.get("availability_on") == "on"

    profile_photo = request.files.get("profile_photo")
    if profile_photo and profile_photo.filename:
        helper.profile_photo = save_upload(profile_photo, "profile_photos")

    db.session.commit()
    flash("Helper profile updated successfully.", "success")
    return redirect(url_for("helper.helper_dashboard"))
