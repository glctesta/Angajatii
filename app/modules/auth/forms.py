import re
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, EmailField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from flask_babel import lazy_gettext as _l

def validate_password_strength(form, field):
    password = field.data
    if len(password) < 8:
        raise ValidationError(_l('Password must be at least 8 characters long.'))
    if not re.search(r'[A-Z]', password):
        raise ValidationError(_l('Password must contain at least one uppercase letter.'))
    if not re.search(r'[a-z]', password):
        raise ValidationError(_l('Password must contain at least one lowercase letter.'))
    if not re.search(r'[0-9]', password):
        raise ValidationError(_l('Password must contain at least one digit.'))
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError(_l('Password must contain at least one special character.'))

class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))

class ForgotPasswordForm(FlaskForm):
    username_or_email = StringField(_l('Username or Email'), validators=[DataRequired()])
    submit = SubmitField(_l('Send Reset Link'))

class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('New Password'), validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField(_l('Confirm Password'), validators=[DataRequired(), EqualTo('password', message=_l('Passwords must match'))])
    submit = SubmitField(_l('Reset Password'))

class ForgotUsernameForm(FlaskForm):
    email = EmailField(_l('Email Address'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Send Username'))

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField(_l('Current Password'), validators=[DataRequired()])
    new_password = PasswordField(_l('New Password'), validators=[DataRequired(), validate_password_strength])
    confirm_password = PasswordField(_l('Confirm New Password'), validators=[DataRequired(), EqualTo('new_password', message=_l('Passwords must match'))])
    submit = SubmitField(_l('Update Password'))
