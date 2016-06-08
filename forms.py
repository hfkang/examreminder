from flask_wtf import Form
from wtforms import StringField, IntegerField, BooleanField, SelectField, RadioField
from wtforms.validators import DataRequired,Length, ValidationError, NumberRange, EqualTo
class PhoneNumber(Form):

    default_area_codes = ('416','647','905')    #GTA codes. i think. probaly best to pull this from an api at some point and update later.

    def __init__(self, area_codes=default_area_codes, message=None):
        self.allowed_codes = area_codes
        self.min = self.max = 10            #only accept standard 10digit phone numbers for the foreseeable future
        if not message:
            message = 'Invalid phone number presented.'
        self.message = message

    def __call__(self, form, field):
        l = field.data and len(field.data) or 0
        number = field.data
        area_code = number[:3]
        print(len(number))
        if l < self.min or l > self.max:
            raise ValidationError(self.message)
        elif not number.isdigit():  #check to see if there are letters or non numeric values in the string
            raise ValidationError(self.message)
        elif not any(area_code in allowed for allowed in self.allowed_codes):  #check to see if the area codes presented are valid (first three char substring in list)
            raise ValidationError(self.message)


class PhoneNumberForm(Form):
    phone = StringField('phone', validators=[DataRequired(),Length(min = 10,max = 10),PhoneNumber()])

class TokenForm(Form):
    token = IntegerField('token',validators=[DataRequired(),NumberRange(min=10000,max=99999)])


class CourseCode(Form):

    def __init__(self, message=None):
        if not message:
            message = 'Invalid course code length.'
        self.message = message
        self.min = 6
        self.max = 9

    def __call__(self, form, field):
        l = field.data and len(field.data) or 0
        code = field.data
        if l < self.min or l > self.max:
            raise ValidationError(self.message)
        elif code[:3].isdigit() or not code[3:6].isdigit():
            self.message = "Alphanumeric error: %s" % code
            print(self.message)
            raise ValidationError(self.message)


class CourseForm(Form):
    course = StringField('course', validators=[DataRequired(),CourseCode()])

class TableManageForm(Form):
    table = SelectField('Table', choices=[('User', 'User'), ('Course', 'Course'), ('Exam', 'Exam')],validators=[DataRequired()])
    action = RadioField('action', validators=[DataRequired()], choices=[('Update','Update'),('Scrape','Scrape'),('Reset','Reset')])
    engineering = BooleanField('engineering')
    artsci = BooleanField('artsci')
    token = StringField('token',validators=[Length(min = 5,max = 5),EqualTo('supplied_token', message='Token must match')])
    supplied_token = StringField('supplied_token',validators=[Length(min = 5,max = 5)])