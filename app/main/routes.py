from flask import render_template, flash, redirect, url_for, request, current_app, Markup
from flask_login import current_user
from app import db
from app.main import bp
from app.models import Post

@bp.route('/')
def index():
    print("Home")
    return render_template('index.html', title='Home')

@bp.route('/blog')
def blogs():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_published.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], True)

    next_url = url_for('main.blogs', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.blogs', page=posts.prev_num) if posts.has_prev else None

    return render_template('blogs.html', 
                            title='Blogs', 
                            page=page, 
                            posts=posts.items,
                            next_url=next_url,
                            prev_url=prev_url,
                            pagination=posts)

@bp.route('/blog/<slug>')
def blog(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    body = Markup(post.html_body)
    return render_template('blog.html', title=post.title, post=post, body=body)