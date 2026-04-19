from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import PasswordField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp


class LoginForm(FlaskForm):
    identifier = StringField("Email or Helper Login ID", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=140)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=140)])
    phone = StringField("Phone", validators=[DataRequired(), Regexp(r"^[0-9+\-\s]{8,20}$", message="Enter a valid phone number")])
    address = TextAreaField("Address", validators=[DataRequired(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    submit = SubmitField("Create Account")


class HelperApplicationForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=140)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=140)])
    mobile_number = StringField("Mobile Number", validators=[DataRequired(), Regexp(r"^[0-9+\-\s]{8,20}$", message="Enter a valid mobile number")])
    address = TextAreaField("Address", validators=[DataRequired(), Length(max=255)])
    city = StringField("City", validators=[DataRequired(), Length(max=120)])
    state = StringField("State", validators=[DataRequired(), Length(max=120)])
    pincode = StringField("Pincode", validators=[DataRequired(), Regexp(r"^[0-9]{4,10}$", message="Enter a valid pincode")])
    aadhaar_number = StringField("Aadhaar Number", validators=[DataRequired(), Regexp(r"^[0-9]{12}$", message="Aadhaar must be 12 digits")])
    profile_photo = FileField("Profile Photo", validators=[Optional(), FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only")])
    skill_category = SelectField(
        "Skill Category",
        validators=[DataRequired()],
        choices=[
            ("Electrician", "Electrician"),
            ("Cleaner", "Cleaner"),
            ("Chef", "Chef"),
            ("Mechanic", "Mechanic"),
            ("Designer", "Designer"),
            ("Painter", "Painter"),
            ("Plumber", "Plumber"),
            ("Carpenter", "Carpenter"),
        ],
    )
    experience = StringField("Experience", validators=[DataRequired(), Regexp(r"^[0-9]{1,2}$", message="Enter experience in years")])
    available_time = StringField("Available Time", validators=[DataRequired(), Length(max=120)])
    short_bio = TextAreaField("Short Bio", validators=[DataRequired(), Length(max=1000)])
    id_proof = FileField("ID Proof", validators=[DataRequired(), FileAllowed(["jpg", "jpeg", "png", "webp", "pdf"], "Images or PDF only")])
    submit = SubmitField("Submit Application")
