from flask_wtf import FlaskForm
from wtforms import StringField, FieldList, FormField
from wtforms.validators import DataRequired

class SzenarioForm(FlaskForm):
    name = StringField("Name")
    start = StringField("Start time", validators=[DataRequired()], description="1h/2m/3s")
    end = StringField("End time", description="1h/2m/3s")

class SzenarioListForm(FlaskForm):
    szenario = FieldList(FormField(SzenarioForm), min_entries=1, max_entries=20)
