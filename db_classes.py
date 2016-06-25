from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
import json
import datetime
import sys
import re
import config as c

db = SQLAlchemy()


class User(UserMixin,db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.Text)
    name = db.Column(db.Text)
    email = db.Column(db.Text)
    social_id = db.Column(db.Text)
    verified = db.Column(db.Boolean)
    token = db.Column(db.Text)
    token_date = db.Column(db.DateTime)

    @classmethod
    def make_unique(cls,name,email,social_id):
        check_id = cls.query.filter_by(social_id = social_id).first()
        if check_id:
            return cls(name,email,social_id)

    def __init__(self,name,email,social_id):
        self.name = name
        self.email = email
        self.social_id = social_id
        self.verified = False

    def __repr__(self):
        return '<User %r>' % self.name

    def check_token(self,token):
        '''
        Takes in a user object and the token they submitted online, and verifies that the token
        Is both correct, and that it has been submitted within 1 hour of creation.
        :param token:
        :return: valid token (boolean)
        '''
        delta = datetime.datetime.now() - self.token_date
        max_age = datetime.timedelta(hours = 1)
        print(type(self.token))
        print(type(token))
        return (self.token == token) and (delta < max_age)


class Course(db.Model):
    id = db.Column(db.Integer,primary_key = True)
    name = db.Column(db.Text)
    date = db.Column(db.Text)
    time = db.Column(db.Text)
    location = db.Column(db.Text)
    faculty = db.Column(db.Text)        #('artsci' or 'eng')
    type = db.Column(db.Text)           #(Engineering only: A,B,C,D,X)

    @property
    def room_assignments(self):
        '''
        returns room locations as a python list for consumption by jinja2
        :return:
        '''
        return json.loads(self.location)

    @classmethod
    def make_unique(cls,name,date,time,location,faculty,type):
        '''
        This method assumes that the U of T does not change course names willy nilly, especially during the year!
        :param name: Course code
        :param date: date of exam
        :param time: time of exam
        :param location: list of exam section and room assignments
        :param faculty: faculty hosting the exam
        :return: course instance
        '''
        check_notif = cls.query.filter_by(name=name).first()
        if check_notif == None:
            return cls(name,date,time,location,faculty,type)

    def __init__(self,name,date,time,location,faculty,type):
        self.name = name
        self.date = date
        self.time = time
        self.location = location
        self.faculty = faculty
        self.type = type

    def __repr__(self):
        return '<Course %s>' % self.name


    def update(self,date,time,location,type):
        self.date = date
        self.time = time
        self.location = location
        self.type = type


class Exam(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer,db.ForeignKey('course.id'))
    course = db.relationship('Course',backref=db.backref('registered'))
    notif = db.Column(db.Text)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    user = db.relationship('User',backref=db.backref('exams'))

    @classmethod
    def make_unique(cls,course, notif, user):
        check_notif = cls.query.filter_by(course=course,notif=notif,user=user).first()
        if check_notif == None:
            return cls(course, notif, user)

    def __init__(self, course, notif, user):
        self.course = course
        self.notif = notif
        self.user = user

    def __repr__(self):
        return '<Exam Reminder %r : %r>' % (self.course.name,self.user_id)


def make_users(db):
    User.__table__.drop(db.engine)
    User.__table__.create(db.engine)

    frank = User.make_unique('Francis Kang', 'h.franciskang@gmail.com', '3478329740891237432')
    sila = User.make_unique( 'Sila Elgin', 'silay@mail.com', '471928328192837198283')
    emily = User.make_unique( 'Emily Qiu', 'faqiu@mail.utoronto.ca', '129328392839283984')

    db.session.add(frank)
    db.session.add(sila)
    db.session.add(emily)

    db.session.commit()


def get_building(room_code):
    building_path = '/app/data/buildings.json'
    if sys.platform == 'darwin':
        building_path = '/Users/fkang/PycharmProjects/examreminder/data/buildings.json'
    with open(building_path, 'r') as f:
        building_list = json.load(f)

    assigned = room_code.split()[0]
    regex = re.compile(assigned)

    for building in building_list:
        if regex.match(building[0]):
            return building



def update_schedule(useArtsci=True,useEngsci=True):
    '''
    Updates the database from the most recent data available
    :return:
    '''
    artsci = {}
    engsci = {}

    if useArtsci:
        with open(c.current_artsci_sched,'r') as f:
            artsci = json.load(f)
    if useEngsci:
        with open(c.current_eng_sched,'r') as f:
            engsci = json.load(f)                   #i can't help myself

    artsci.update(engsci)
    sched = artsci

    for course in sched:
        rooms, date, time, faculty, exam_type = sched[course]
        rooms = json.dumps(rooms)

        course_obj = Course.query.filter_by(name=course).first()
        if course_obj:
            course_obj.update(date,time,rooms,exam_type)
        else:
            course_obj = Course.make_unique(course,date,time,rooms,faculty,exam_type)
            db.session.add(course_obj)
    db.session.commit()

def match_schedule(course,*args):
    '''
    DEPRECATED
    This was used when update_courses pulled the list from the changes.json, and it needed to be determined which
    dictionary to source our data from.
    :param course:
    :param args:
    :return:
    '''
    for sched in args:
        if course in sched:
            return sched
    else:
        return None     # Course not found. It has probably been deleted from the online registry

def delete_user(user):
    Exam.query.filter_by(user = user).delete()
    db.session.delete(user)
    db.session.commit()
    return 0

def reset_table(table):
    try:
        table.__table__.drop(db.engine)
    except:
        pass
    table.__table__.create(db.engine)

if __name__ == '__main__':
    from exams import app
    with app.test_request_context():
        #reset_table(Course)
        update_schedule()
        print(Course.query.all())
        #print(Exam.query.all())
        #print(User.query.filter_by(name='Francis Kang')[1].social_id)
