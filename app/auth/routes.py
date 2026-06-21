from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Goal
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from itsdangerous import URLSafeTimedSerializer

def send_reset_email(email, reset_url):
    mail_server = os.getenv('MAIL_SERVER')
    mail_port = os.getenv('MAIL_PORT')
    mail_use_tls = os.getenv('MAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
    mail_username = os.getenv('MAIL_USERNAME')
    mail_password = os.getenv('MAIL_PASSWORD')
    mail_sender = os.getenv('MAIL_DEFAULT_SENDER', mail_username)

    subject = "Password Reset Request - CreatorOS"
    body = f"""Hello,

You requested a password reset for your CreatorOS workspace account.
Please click the link below or copy and paste it into your browser to reset your password:

{reset_url}

This link is valid for 1 hour. If you did not request this reset, please ignore this email.

Best regards,
The CreatorOS Team
"""

    if mail_server and mail_port and mail_username and mail_password:
        try:
            msg = MIMEMultipart()
            msg['From'] = mail_sender
            msg['To'] = email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))

            port = int(mail_port)
            if mail_use_tls:
                server = smtplib.SMTP(mail_server, port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(mail_server, port)
            
            server.login(mail_username, mail_password)
            server.sendmail(mail_sender, email, msg.as_string())
            server.quit()
            print(f"[MAIL SUCCESS] Password recovery mail sent successfully to {email}.")
            return True
        except Exception as e:
            print(f"[MAIL ERROR] Failed to send email via SMTP: {str(e)}")

    print("--------------------------------------------------")
    print(f"[MAIL FALLBACK] Forgot Password Request for {email}")
    print(f"Reset Link: {reset_url}")
    print("--------------------------------------------------")

    try:
        log_path = r"c:\Users\NITHIN KATA\Downloads\Creator_Os\recovery_emails.txt"
        with open(log_path, 'a', encoding='utf-8') as f:
            from datetime import datetime
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"To: {email}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"Reset Link: {reset_url}\n")
            f.write("-" * 50 + "\n")
    except Exception as fe:
        print(f"[FILE LOG ERROR] Failed to write recovery log: {str(fe)}")

    return False

auth = Blueprint('auth', __name__)

@auth.route('/landing')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('auth/landing.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Validation
        if not name or not email or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('auth.register'))
            
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email address already registered.', 'danger')
            return redirect(url_for('auth.register'))
            
        new_user = User(name=name, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        flash('Registration successful! Let\'s set up your profile.', 'success')
        return redirect(url_for('dashboard.onboarding'))
        
    return render_template('auth/register.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user, remember=remember)
        
        # Check if onboarding is needed
        if not user.goal:
            return redirect(url_for('dashboard.onboarding'))
            
        return redirect(url_for('dashboard.index'))
        
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have logged out.', 'info')
    return redirect(url_for('auth.landing'))

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
            token = serializer.dumps(email, salt='password-reset-salt')
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            sent_via_smtp = send_reset_email(email, reset_url)
            if sent_via_smtp:
                flash('Password reset instructions have been sent to your email.', 'success')
            else:
                flash('Recovery link generated! Since local email configuration is missing or inactive, we logged the details to terminal and recovery_emails.txt in the project directory.', 'info')
        else:
            print(f"[MAIL INFO] Reset request for non-existent email: {email}")
            flash('If that email exists in our system, password reset instructions have been sent.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_password.html')

@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))
        
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('auth/reset_password.html', token=token)
            
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)
            
        user.set_password(password)
        db.session.commit()
        
        flash('Your password has been successfully reset! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', token=token)
