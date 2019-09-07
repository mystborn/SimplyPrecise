from flask import render_template, redirect, url_for, flash, request
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.cms import bp
from app.cms.forms import LoginForm, RegistrationForm, PostForm
from app.models import User
from app.email import send_email

def send_account_verification_email(user, expires_in=600):
    """
    Unlike most sites, the user account verification goes to
    the site admins instead of to the user themselves.
    """

    token = jwt.encode(
        {'verify': user.id, 'exp': time() + expires_in},
        app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    send_email('[Simply Precise] New User Request',
        sender=app.config['MAIL_USERNAME'],
        recipients=app.config['ADMINS'],
        text_body=render_template('verify_account.txt',
                                  user=user, token=token),
        html_body=render_template('verify_account.html',
                                  user=user, token=token))

@bp.route('/register', methods=['GET', 'POST'])
def register_user():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, is_verified=False)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Please wait for an admin to verify your account.')
        return redirect(url_for('cms.login'))
    render_template('register.html', title='Register', form=form)


@bp.route('/verify_account/<token>')
def verify_account(token):
    user_id = None
    try:
        user_id = jwt.decode(token, app.config['SECRET_KEY'],
                             algorithms=['HS256'])['verify']
    except:
        pass

    user = User.query.filter_by(id=user_id)
    if user.is_verified:
        return render_template('account_verified.html', title='Account Verification', 
                               message=f'User {user.username} already verified')
    else
        user.is_verified = True
        session.commit()
        return render_template('account_verified.html', title='Account Verification', 
                               message=f'User {user.username} has been verified')



@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('cms.login'))
        elif not user.is_verified:
            flash('You have not been verified by an admin yet. Please wait for an admin to approve your account.')
            return redirect(url_for('cms.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page.netloc != ''):
            next_page = url_for('main.index')
        flash('You are now logged in!')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))