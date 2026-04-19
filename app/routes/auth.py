from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.extensions import db
from app.forms.auth_forms import LoginForm, RegisterForm
from app.models.helper import Helper
from app.models.user import User


auth_bp = Blueprint("auth", __name__)


def _dashboard_for_role(user: User) -> str:
    if user.role == "admin":
        return url_for("admin.dashboard")
    if user.role == "helper":
        return url_for("helper.helper_dashboard")
    return url_for("helper.customer_dashboard")


@auth_bp.route("/")
def home():
    return render_template("home.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(_dashboard_for_role(current_user))

    form = LoginForm()
    if form.validate_on_submit():
        identifier = form.identifier.data.strip().lower()
        password = form.password.data

        user = User.query.filter(User.email == identifier).first()
        if identifier == "admin" and user is None:
            user = User.query.filter(User.role == "admin", User.email.in_(["admin", "admin@localift.com"])).first()

        if user and user.is_active and user.check_password(password):
            login_user(user)
            user.last_login_at = datetime.utcnow()
            if user.helper_profile:
                user.helper_profile.last_login_at = datetime.utcnow()
            db.session.commit()
            flash("Welcome back.", "success")
            next_url = request.args.get("next")
            return redirect(next_url or _dashboard_for_role(user))

        helper = Helper.query.filter(Helper.login_id == identifier.upper()).first()
        if helper and helper.status == "active" and helper.user.is_active and helper.user.check_password(password):
            login_user(helper.user)
            helper.user.last_login_at = datetime.utcnow()
            helper.last_login_at = datetime.utcnow()
            db.session.commit()
            flash("Helper login successful.", "success")
            return redirect(url_for("helper.helper_dashboard"))

        flash("Invalid credentials.", "error")

    return render_template("login.html", form=form)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(_dashboard_for_role(current_user))

    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template("register.html", form=form)

        if form.phone.data and User.query.filter_by(phone=form.phone.data.strip()).first():
            flash("Phone number already registered.", "error")
            return render_template("register.html", form=form)

        user = User(
            full_name=form.full_name.data.strip(),
            email=email,
            phone=form.phone.data.strip(),
            address=form.address.data.strip(),
            role="customer",
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash("Account created. You can log in now.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("auth.home"))
