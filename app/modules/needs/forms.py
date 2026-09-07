from flask_wtf import FlaskForm
from wtforms import IntegerField, DateField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional
from flask_babel import lazy_gettext as _

class ResourceNeedForm(FlaskForm):
    sub_cdc = SelectField(_('Sub Department'), coerce=int, validators=[DataRequired()])
    function = SelectField(_('Function'), coerce=int, validators=[DataRequired()])
    shift = SelectField(_('Shift'), coerce=int, validators=[Optional()])
    required_headcount = IntegerField(_('Required Headcount'), validators=[DataRequired()])
    min_headcount = IntegerField(_('Min Headcount'), validators=[Optional()])
    effective_from = DateField(_('Effective From'), validators=[DataRequired()])
    notes = TextAreaField(_('Notes'), validators=[Optional()])
    submit = SubmitField(_('Save'))

class ResourceRequestForm(FlaskForm):
    sub_cdc = SelectField(_('Sub Department'), coerce=int, validators=[DataRequired()])
    function = SelectField(_('Function'), coerce=int, validators=[DataRequired()])
    requested_count = IntegerField(_('Requested Count'), validators=[DataRequired()])
    priority = SelectField(_('Priority'), choices=[('low', _('Low')), ('normal', _('Normal')), ('high', _('High')), ('critical', _('Critical'))], validators=[DataRequired()])
    reason = TextAreaField(_('Reason'), validators=[Optional()])
    submit = SubmitField(_('Submit'))

class NeedFilterForm(FlaskForm):
    department = SelectField(_('Department'), coerce=int, validators=[Optional()])
    function = SelectField(_('Function'), coerce=int, validators=[Optional()])
    shift = SelectField(_('Shift'), coerce=int, validators=[Optional()])
    submit = SubmitField(_('Filter'))
