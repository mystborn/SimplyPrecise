from flask import render_template, redirect, url_for, flash, request, current_app
from werkzeug import secure_filename
from werkzeug.urls import url_parse
from flask_login import login_user, logout_user, current_user, login_required
from app import db
from app.cms import bp
from app.cms.forms import LoginForm, RegistrationForm, PostForm, UserForm
from app.models import UserLevel, User, Post, Tag
from app.email import send_email
from pyquery import PyQuery as pq
from datetime import datetime
from time import time
import os

import jwt

def send_account_verification_email(user, expires_in=600):
    """
    Unlike most sites, the user account verification goes to
    the site admins instead of to the user themselves.
    """

    token = jwt.encode(
        {'verify': user.id, 'exp': time() + expires_in},
        current_app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    send_email('[Simply Precise] New User Request',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=current_app.config['ADMINS'],
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
        user.level = UserLevel.normal
        db.session.add(user)
        db.session.commit()
        flash('Please wait for an admin to verify your account.')
        send_account_verification_email(user)
        return redirect(url_for('cms.login'))
    return render_template('register.html', title='Register', form=form)


@bp.route('/verify_account/<token>')
def verify_account(token):
    user_id = None
    try:
        user_id = jwt.decode(token, current_app.config['SECRET_KEY'],
                             algorithms=['HS256'])['verify']
    except:
        pass

    user = User.query.filter_by(id=user_id).first()
    if user == None:
        return render_template('account_verified', title='Account Verification',
                               message=f'The requested user id does not exist')
    elif user.is_verified:
        return render_template('account_verified.html', title='Account Verification', 
                               message=f'User {user.username} already verified')
    else:
        user.is_verified = True
        db.session.commit()
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
            flash('Invalid username or password', 'danger')
            return redirect(url_for('cms.login'))
        elif not user.is_verified:
            flash('You have not been verified by an admin yet. Please wait for an admin to approve your account.', 'danger')
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

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = UserForm()
    user = current_user

    if form.validate_on_submit():
        user.name = form.name.data
        user.about_me = form.about_me.data
        if form.avatar.data:
            path = f'app/static/images/avatars/{user.id}'
            if not os.path.exists(path):
                os.makedirs(path)
            form.image.save(f'{path}/avatar.png')
            user.has_avatar = True
        db.session.commit()
        return redirect(url_for('main.member', username=user.username))

    if user.name:
        form.name.data = user.name

    if user.about_me:
        form.about_me.data = user.about_me

    if user.has_avatar:
        avatar = url_for('static', filename=f'images/avatars/{user.id}/avatar.png')
    else:
        avatar = url_for('static', filename='images/avatars/default.svg')

    return render_template('edit_profile.html', 
                           title='Edit Profile', 
                           form=form, 
                           avatar=avatar,
                           user=user)
    

def fill_post_from_form(post, form):
    post.title = form.title.data
    print(form.body)
    post.markdown_body = form.body.data
    post.tags = Tag.validate_tags(form.tags.data)
    post.prepare_to_save()

    if not form.summary.data:
        html = pq(post.html_body)
        first_para = html('p:first')
        if first_para:
            post.summary = first_para[0].text
    else:
        post.summary = form.summary.data

    if post.author == None:
        post.author = current_user
    else:
        post.date_edited = datetime.utcnow()


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def blog_create():
    form = PostForm()
    if form.validate_on_submit():
        if Post.query.filter_by(title=form.title.data).first() != None:
            flash('Blog with that title already exists.', 'danger')
        else:
            post = Post()
            fill_post_from_form(post, form)

            db.session.add(post)
            db.session.commit()
            return redirect(url_for('main.index', slug=post.slug))
    return render_template('blog_create.html', title='Create Blog', form=form)

@bp.route('/edit', methods=['GET', 'POST'])
@login_required
def blog_edit():
    post_id = request.args.get('id', -1, type=int)
    if post_id == -1:
        return redirect(url_for('main.index'))

    post = Post.query.filter_by(id=post_id).first()

    if post == None or (current_user.level != UserLevel.admin and post.author != current_user):
        return redirect(url_for('main.index'))

    form = PostForm()
    if form.validate_on_submit():
        if post.title != form.title.data and Post.query.filter_by(title=form.title.data).first() != None:
            flash('Blog with that title already exists.', 'danger')
        else:
            fill_post_from_form(post, form)
            db.session.commit()

            return redirect(url_for('main.index', slug=post.slug))

    form.title.data = post.title
    form.body.data = post.markdown_body
    form.tags.data = ' '.join(map(lambda t: t.title, post.tags))
    return render_template('blog_create.html', title='Edit Blog', form=form)