from flask import render_template, flash, redirect, url_for, request, current_app, Markup
from flask_login import current_user
from app import db
from app.main import bp
from app.main.forms import SearchForm
from app.models import Post, Tag, User
from sqlalchemy import func
from urllib import parse

@bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_published.desc()).paginate(page, current_app.config['POSTS_PER_PAGE'], True)

    next_url = url_for('main.index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.index', page=posts.prev_num) if posts.has_prev else None

    return render_template('blogs.html', 
                            title='Home', 
                            page=page, 
                            posts=posts.items,
                            next_url=next_url,
                            prev_url=prev_url,
                            pagination=posts)

@bp.route('/about')
def about():
    users = User.query.order_by(User.level.desc()).all()
    return render_template('about.html', title='About', members=users)


@bp.route('/blog/<slug>')
def blog(slug):
    post = Post.query.filter_by(slug=slug).first_or_404()
    body = Markup(post.html_body)
    return render_template('blog.html', title=post.title, post=post, body=body)

@bp.route('/member/<username>')
def member(username):
    member = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.date_published.desc()) \
                      .filter_by(user_id=member.id) \
                      .paginate(page, current_app.config['POSTS_PER_PAGE'], True)

    next_url = url_for('main.member', username=username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.member', username=username, page=posts.prev_num) if posts.has_prev else None

    return render_template('member_profile.html',
                           title=member.name if member.name else username,
                           member=member,
                           page=page,
                           posts=posts.items,
                           next_url=next_url,
                           prev_url=prev_url,
                           pagination=posts)

@bp.route('/searchbar', methods=['POST'])
def searchbar():
    if request.form.get('search', '') != '':
        return redirect(url_for('main.search', q=request.form['search']))
    else:
        return redirect(url_for('main.search'))

@bp.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()

    if form.validate_on_submit():
        query = form.query.data
        tags = form.tags.data
        tag_all = False if form.tags_inclusive.data == 'Any' else True
    else:
        query = parse.unquote_plus(request.args.get('q', ''))
        tags = parse.unquote_plus(request.args.get('t', ''))
        form.query.data = query
        form.tags.data = tags
        tag_all = False

    if not query and not tags:
        return render_template('new_search.html', title='Search', form=form)
    else:
        items = None
        if query:
            items = Post.query.search(query, sort=True)
        else:
            items = Post.query

        if tags:
            tags = list(filter(None, tags.split(' ')))
            old_len = len(tags)
            tags = Tag.get_valid(tags)
            new_len = len(tags)

            if (new_len == 0 and query == '') or (tag_all and old_len != new_len):
                items = None
            else:
                items = items.join(Post.tags) \
                             .filter(Tag.id.in_(map(lambda t: t.id, tags)))
    
                if tag_all:
                    items = items.group_by(Post.id) \
                                 .having(func.count(Tag.id) == len(tags))


    if items == None:
        return render_template('no_search_results.html', title='Search', form=form)

    page = request.args.get('p', 1, type=int)
    posts = items.paginate(page, current_app.config['POSTS_PER_PAGE'], True)

    if len(posts.items) == 0:
        return render_template('no_search_results.html', title='Search', form=form)

    next_url = url_for('main.search', p=posts.next_num) if posts.has_next else None
    prev_url = url_for('main.search', p=posts.prev_num) if posts.has_prev else None

    return render_template('search.html', 
                           title='Search',
                           form=form,
                           page = page,
                           posts=posts.items,
                           next_url=next_url,
                           prev_url=prev_url,
                           pagination=posts)