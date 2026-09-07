from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, SelectField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from flask_babel import lazy_gettext as _l

class ImportForm(FlaskForm):
    source_type = SelectField(_l('Source Type'), choices=[('employee_db', _l('Employee Database')), ('file', _l('File Upload')), ('api', _l('API'))], validators=[DataRequired()])
    file = FileField(_l('File'), validators=[FileAllowed(['csv', 'json'], 'CSV and JSON only!')])
    submit = SubmitField(_l('Start Import'))

class UserCreateForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField(_l('Confirm Password'), validators=[DataRequired(), EqualTo('password')])
    role = SelectField(_l('Role'), coerce=int, validators=[DataRequired()])
    preferred_language = SelectField(_l('Preferred Language'), choices=[('en', 'English'), ('it', 'Italiano'), ('ro', 'Romana')], validators=[DataRequired()])
    submit = SubmitField(_l('Create User'))

class UserEditForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    role = SelectField(_l('Role'), coerce=int, validators=[DataRequired()])
    preferred_language = SelectField(_l('Preferred Language'), choices=[('en', 'English'), ('it', 'Italiano'), ('ro', 'Romana')], validators=[DataRequired()])
    is_active = BooleanField(_l('Active'))
    submit = SubmitField(_l('Update User'))
