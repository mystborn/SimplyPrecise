from flask import current_app, Markup, abort
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login
from markdown import markdown
from markdown.extensions.codehilite import CodeHiliteExtension
from flask_sqlalchemy import BaseQuery
from sqlalchemy_searchable import SearchQueryMixin, make_searchable
from sqlalchemy_utils.types import TSVectorType
from datetime import datetime
import re
from enum import Enum
from functools import total_ordering

make_searchable(db.metadata)

@total_ordering
class UserLevel(Enum):
    normal = 0
    moderator = 1
    admin = 2

    def __lt__(self, other):
        if self.__class__ is other.__class__:
            return self.value < other.value
        return NotImplemented

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    email = db.Column(db.UnicodeText)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.Text)
    level = db.Column(db.Enum(UserLevel))
    is_verified = db.Column(db.Boolean)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login.user_loader
def load_user(id):
    user = User.query.get(int(id))
    if user != None and user.is_verified:
        return user
    return None


tag_to_post = db.Table('tags',
    db.Column('post_id', db.Integer, db.ForeignKey('post.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id')))

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), index=True)

    @staticmethod
    def validate_tags(tag_string):
        tags = []
        for split in tag_string.split(' '):
            if split == '':
                continue

            tag = Tag.query.filter_by(title=split).first()
            if tag == None:
                tag = Tag(title=split)
                db.session.add(tag)
            tags.append(tag)
        return list(set(tags))

    def __repr__(self):
        return f'<Tag {self.title}>'


class PostQuery(BaseQuery, SearchQueryMixin):
    pass

class Post(db.Model):
    query_class = PostQuery

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Unicode(255))
    slug = db.Column(db.Text, index=True)
    summary = db.Column(db.UnicodeText)
    html_body = db.Column(db.UnicodeText)
    markdown_body = db.Column(db.UnicodeText)
    date_published = db.Column(db.DateTime, index=True)
    date_edited = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    tags = db.relationship('Tag', secondary=tag_to_post, backref=db.backref('posts', lazy='dynamic'), passive_deletes=True)
    search_vector = db.Column(TSVectorType('title', 'summary', 'markdown_body', weights={'title': 'A', 'summary': 'B', 'markdown_body': 'C'}))

    def __init__(self, *args, **kwargs):
        super(Post, self).__init__(*args, **kwargs)
        self.date_edited = self.date_published = datetime.utcnow()

    def prepare_to_save(self):
        self.slug = re.sub('[^\\w]+', '-', self.title.lower())

        hilite = CodeHiliteExtension(linenums=False, css_class='highlight')
        markdown_text = markdown(self.markdown_body, extensions=[hilite, 'fenced_code'])
        self.html_body = Markup(markdown_text)