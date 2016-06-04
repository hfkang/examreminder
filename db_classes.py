from flask.ext.login import UserMixin
from flask_sqlalchemy import SQLAlchemy
import json
import datetime
import sys
import re

SCHED_URL = 'examsched.json'
ARTSCI_SCHED_URL = 'artsci_sched.json'

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
        if check_id == None:
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


    @property
    def room_assignments(self):
        '''
        returns room locations as a python list for consumption by jinja2
        :return:
        '''
        return json.loads(self.location)

    def __init__(self,name,date="whenever",time="whenever",location = "wherever"):
        self.name = name
        self.date = date
        self.time = time
        self.location = location

    def __repr__(self):
        return '<Course %s>' % self.name


    def update(self,date,time,location):
        self.date = date
        self.time = time
        self.location = location



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

def test_dup():
    dupfran  = User.make_unique('4164340089','Francis Kang',b'lmao')
    dupnum = User.make_unique('4164340089','Francissdf Kang',b'lmao')
    unique = User.make_unique('416xxx0000','Unique Snowflake',b'lmaobutts')
    print(dupfran)
    print(dupnum)
    print(unique)

    aer = Course.query.filter_by(name = 'AER201').first()
    reminder = Exam.make_unique(aer, 'dayof', User.query.first())
    print(reminder)
    if reminder != None:
        db.session.add(reminder)
        db.session.commit()

def import_data():
    '''
    Ingests the complete exam schedule as outputted by the download.py scripts
    Avoid using after the notification table has entires, as the course ordering /may/ shift! rip foreign keys
    :return:
    '''

    drop_table(Course)

    with open(SCHED_URL, 'r') as f:
        sched = json.load(f)

    for code in sched:
        date,time,rooms = ingest_engsci(code, sched)
        exam = Course(code, date=date, time=time, location=rooms)
        db.session.add(exam)


    with open(ARTSCI_SCHED_URL, 'r') as f:
        sched = json.load(f)

    for course_code in sched:
        date,time,rooms = ingest_artsci(course_code,sched)
        exam = Course(course_code, date=date, time=time, location=rooms)
        db.session.add(exam)

    db.session.commit()

def get_building(room_code):
    building_path = '/home/francis/examreminder/data/buildings.json'
    if sys.platform == 'darwin':
        building_path = '/Users/fkang/PycharmProjects/examreminder/data/buildings.json'
    with open(building_path, 'r') as f:
        building_list = json.load(f)

    assigned = room_code.split()[0]
    regex = re.compile(assigned)

    for building in building_list:
        if regex.match(building[0]):
            return building




def ingest_engsci(exam,exam_dict):
    '''
    This is just so that we can have symmetic methods between the artsci and engsci scheudles
    :param exam:
    :param exam_dict:
    :return: date,time,rooms as pulled straight out of the json
    '''
    date = exam_dict[exam]['date']
    time = exam_dict[exam]['time']
    room_dict = exam_dict[exam]['rooms']

    for room in room_dict:
        room[2] = get_building(room[1])

    rooms = json.dumps(room_dict)

    return date,time,rooms

def ingest_artsci(exam,exam_dict):
    exam_data = exam_dict[exam][0]
    time = exam_data[2][:7].replace("EV", "PM")
    # Artsci calendar has format (DAY DD MON) Convert to engineering format (MON DD)
    # It also stores the time like PM 2:00 , and seems to have start times of 9am, 2pm, and 7pm only

    date_obj = datetime.datetime.strptime(exam_data[1] + time, '%a %d %b%p %I:%M')
    date = date_obj.strftime('%b %d')
    time = date_obj.strftime('%I:%M %p')
    rooms = json.dumps([[section[0], section[3],get_building(section[3])] for section in exam_dict[exam]])

    return date,time,rooms

def update_schedule():
    with open('changes.json','r') as f:
        delta = json.load(f)
    with open(ARTSCI_SCHED_URL,'r') as f:
        artsci = json.load(f)
    with open(SCHED_URL,'r') as f:
        engsci = json.load(f)                   #i cna't help myself

    for course in delta:
        sched = match_schedule(course,artsci,engsci)
        course_obj = Course.query.filter_by(name=course).first()
        if sched == artsci:
            print("In artsci land")
            date,time,rooms = ingest_artsci(course,sched)
            print(date,time,rooms)
        elif sched == engsci:
            print("In eng land ")
            date,time,rooms = ingest_engsci(course,sched)
            print(date,time,rooms)
        course_obj.update(date, time, rooms)

    db.session.commit()


def match_schedule(course,*args):
    for sched in args:
        if course in sched:
            return sched



def delete_user(user):
    Exam.query.filter_by(user = user).delete()
    db.session.delete(user)
    db.session.commit()
    return 0



def drop_table(table):
    from exams import app
    with app.test_request_context():
        table.__table__.drop(db.engine)
        table.__table__.create(db.engine)

if __name__ == '__main__':
    #drop_table(Exam)
    from exams import app
    with app.test_request_context():
        #update_schedule()
        print(Exam.query.all())
        print(User.query.filter_by(name='Francis Kang')[1].social_id)
