from flask_wtf import FlaskForm, RecaptchaField
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SubmitField, IntegerField, BooleanField, PasswordField
from wtforms.validators import ValidationError, DataRequired, Length, Email, EqualTo
from app.models import User, Post
from PIL import Image

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    body = StringField('Body', validators=[DataRequired()])
    tags = StringField('Tags')
    summary = TextAreaField('Summary')
    submit = SubmitField('Submit')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Verify Password', validators=[DataRequired(), EqualTo('password')])
    recaptcha = RecaptchaField()
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already taken.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already used.')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class UserForm(FlaskForm):
    name = StringField('Display Name', default='', validators=[Length(max=128)])
    about_me = TextAreaField('About Me', default='', validators=[Length(max=10000)])
    avatar = FileField('Avatar', validators=[FileAllowed(['png', 'jpg', 'jpeg'], 'Must be an image file.')])
    submit = SubmitField('Save Changes')

    def validate_avatar(self, avatar):
        if avatar.data is not None:
            try:
                self.image = Image.open(avatar.data.stream)
                if self.image.size != (200, 200):
                    self.image = image.resize((200, 200))
            except(IOError, ValueError):
                raise ValidationError('Error opening or processing image')