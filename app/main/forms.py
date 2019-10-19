from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, SubmitField
from wtforms.validators import DataRequired

class SearchForm(FlaskForm):
    query = StringField('Search')
    tags = StringField('Tags')
    tags_inclusive = RadioField('All Tags?', default='All', choices=[('All', 'All'), ('Any', 'Any')])
    submit = SubmitField('Search')