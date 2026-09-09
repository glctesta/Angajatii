import sys, os
from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, current_user, login_required
from flask_babel import _
from . import auth_bp
from .forms import LoginForm, ForgotPasswordForm, ResetPasswordForm, ForgotUsernameForm, ChangePasswordForm
from app.extensions import db
from app.models.auth import User, PasswordResetToken
from app.services.audit_service import log_action
from sqlalchemy import or_

# Add root to sys.path to import email_connector
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from email_connector import EmailSender

def validate_password_strength(password):
    errors = []
    if len(password) < 8:
        errors.append(_('Minimo 8 caratteri'))
    if not any(c.isupper() for c in password):
        errors.append(_('Almeno una lettera maiuscola'))
    if not any(c.islower() for c in password):
        errors.append(_('Almeno una lettera minuscola'))
    if not any(c.isdigit() for c in password):
        errors.append(_('Almeno un numero'))
    if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        errors.append(_('Almeno un carattere speciale'))
    return errors

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if 'current_company_id' not in session:
            return redirect(url_for('auth.select_company'))
        return redirect(url_for('dashboard.index'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(Username=form.username.data).first()
        
        if user:
            if user.is_locked_out:
                flash(_('Account bloccato. Riprova più tardi.'), 'error')
                return render_template('auth/login.html', form=form)
                
            if user.check_password(form.password.data):
                user.record_successful_login()
                db.session.commit()
                login_user(user, remember=form.remember_me.data)
                
                log_action(user.UserId, 'LOGIN', 'auth')
                
                if user.MustChangePassword:
                    return redirect(url_for('auth.change_password'))

                # Redirect to company selection
                return redirect(url_for('auth.select_company'))
            else:
                user.record_failed_login()
                db.session.commit()
                
        flash(_('Username o password non validi'), 'error')
        
    return render_template('auth/login.html', form=form)


@auth_bp.route('/select-company', methods=['GET', 'POST'])
@login_required
def select_company():
    """Select which company to work with for this session."""
    from app.models.organization import Employeer
    from app.models.employee import EmployeeHireHistory

    # Get accessible companies
    if current_user.can_see_all_companies:
        companies = db.session.query(Employeer).filter(
            Employeer.DateOut.is_(None)
        ).order_by(Employeer.EmployeerName).all()
    else:
        company_ids = current_user.get_accessible_company_ids()
        if not company_ids:
            flash(_('Nessuna societa assegnata. Contattare l\'amministratore.'), 'error')
            return redirect(url_for('auth.login'))
        companies = db.session.query(Employeer).filter(
            Employeer.EmployeerId.in_(company_ids),
            Employeer.DateOut.is_(None)
        ).order_by(Employeer.EmployeerName).all()

    # Auto-select if only one company
    if len(companies) == 1:
        session['current_company_id'] = companies[0].EmployeerId
        session['current_company_name'] = companies[0].EmployeerName
        next_page = request.args.get('next')
        return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        company_id = request.form.get('company_id')
        if company_id:
            company_id = int(company_id)
            # Verify access
            allowed_ids = [c.EmployeerId for c in companies]
            if company_id in allowed_ids:
                company = next(c for c in companies if c.EmployeerId == company_id)
                session['current_company_id'] = company_id
                session['current_company_name'] = company.EmployeerName
                log_action(current_user.UserId, f'SELECT_COMPANY:{company.EmployeerName}', 'auth')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('dashboard.index'))

    return render_template('auth/select_company.html', companies=companies)

@auth_bp.route('/logout')
@login_required
def logout():
    log_action(current_user.UserId, 'LOGOUT', 'auth')
    logout_user()
    session.pop('current_company_id', None)
    session.pop('current_company_name', None)
    flash(_('Sei stato disconnesso.'), 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/change-language', methods=['POST'])
def change_language():
    lang = request.form.get('language')
    if lang in ['it', 'en', 'ro', 'es', 'fr', 'de']:
        session['language'] = lang
    return redirect(request.referrer or url_for('dashboard.index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter(
            or_(User.Username == form.username_or_email.data, User.Email == form.username_or_email.data)
        ).first()
        
        if user and user.Email:
            token = PasswordResetToken.generate_token(user.UserId, db.session)
            
            try:
                sender = EmailSender('email_key.key', 'email_credentials.enc')
                reset_url = url_for('auth.reset_password', token=token, _external=True)
                sender.send_email(
                    to=user.Email,
                    subject=_('Ripristino Password'),
                    body=f"Usa questo link per reimpostare la tua password: {reset_url}"
                )
                log_action(user.UserId, 'PASSWORD_RESET_REQUEST', 'auth')
            except Exception as e:
                current_app.logger.error(f"Failed to send reset email: {e}")
                
        flash(_("Se l'account esiste, è stata inviata un'email con il link per reimpostare la password."), 'info')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    reset_token = db.session.query(PasswordResetToken).filter_by(Token=token).first()
    
    if not reset_token or not reset_token.is_valid:
        flash(_('Il link per il ripristino della password non è valido o è scaduto.'), 'error')
        return redirect(url_for('auth.forgot_password'))
        
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = reset_token.user
        errors = validate_password_strength(form.password.data)
        if errors:
            for err in errors:
                flash(err, 'error')
            return render_template('auth/reset_password.html', form=form)
            
        user.set_password(form.password.data)
        user.MustChangePassword = False
        reset_token.mark_used()
        db.session.commit()
        
        log_action(user.UserId, 'PASSWORD_RESET', 'auth')
        
        flash(_('La tua password è stata reimpostata. Ora puoi accedere.'), 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', form=form)

@auth_bp.route('/forgot-username', methods=['GET', 'POST'])
def forgot_username():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    form = ForgotUsernameForm()
    if form.validate_on_submit():
        user = db.session.query(User).filter_by(Email=form.email.data).first()
        
        if user and user.Email:
            try:
                sender = EmailSender('email_key.key', 'email_credentials.enc')
                sender.send_email(
                    to=user.Email,
                    subject=_('Recupero Username'),
                    body=f"Il tuo username è: {user.Username}"
                )
                log_action(user.UserId, 'USERNAME_RECOVERY', 'auth')
            except Exception as e:
                current_app.logger.error(f"Failed to send username recovery email: {e}")
                
        flash(_("Se l'email esiste nei nostri sistemi, ti abbiamo inviato il tuo username."), 'info')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_username.html', form=form)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash(_('La password corrente non è corretta.'), 'error')
            return render_template('auth/change_password.html', form=form)
            
        errors = validate_password_strength(form.new_password.data)
        if errors:
            for err in errors:
                flash(err, 'error')
            return render_template('auth/change_password.html', form=form)
            
        current_user.set_password(form.new_password.data)
        was_forced = current_user.MustChangePassword
        current_user.MustChangePassword = False
        db.session.commit()
        
        log_action(current_user.UserId, 'PASSWORD_CHANGE', 'auth')
        
        flash(_('La tua password è stata aggiornata con successo.'), 'success')
        if was_forced:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.profile'))
        
    return render_template('auth/change_password.html', form=form)

@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)
