from flask import Flask, redirect, url_for, session,render_template,flash
from flask_oauthlib.client import OAuth, OAuthException
from flask_login import LoginManager, login_user,current_user,login_required
import random,datetime
from forms import PhoneNumberForm,TokenForm,CourseForm
from functools import wraps
from db_classes import User, Course, Exam, db, delete_user

app = Flask(__name__)
app.config.from_object('config')     #set as envar in local windows environment.
db.init_app(app)

oauth = OAuth()
oauth.init_app(app)

lm = LoginManager(app)
lm.login_view = "new_user"

DEFAULT_NOTIF = 'dayof'



google = oauth.remote_app(
    'google',
    app_key = 'GOOGLE',
    request_token_params={
        'scope': 'email'
    },
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)


def verified_users(func):
    @wraps(func)
    def verify(*args,**kwargs):
        if not current_user.verified:
            return redirect(url_for('register'))
        return func(*args,**kwargs)
    return verify



def update_token(user):
    token = random.randrange(10000, 99999)      #generate 5 digit number w/o leading 0
    now = datetime.datetime.now()
    user.token = token

    '''
    This is the part where you use the plivo api to send a token to the user's phoen number.
    Actually we could always just send them emails but that would be pretty lame. LAME.
    '''

    user.token_date = now
    db.session.commit()



@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/')
def new_user():
    if not current_user.is_anonymous:
        return redirect(url_for('home'))
    return render_template('welcome.html')


@app.route('/login')
def login():
    callback = url_for('authorized',_external = True)
    return google.authorize(callback=callback)

@app.route('/login/authorized')
@google.authorized_handler
def authorized(resp):
    if resp is None:
        return redirect(url_for('new_user'))

    if isinstance(resp, OAuthException):
        return 'Error: %s' % resp

    session['google_token'] = (resp['access_token'], '')
    me = google.get('userinfo')
    social_id = me.data['id']
    username = me.data['name']
    email = me.data['email']

    if social_id is None:
        flash('Authentication failed.')
        return redirect(url_for('new_user'))

    user = User.query.filter_by(social_id=social_id).first()
    if not user:
        user = User.make_unique(username,email,social_id)
        db.session.add(user)
        db.session.commit()

    login_user(user, True)
    return redirect(url_for('register'))        #home is for logged in users

@app.route('/home', methods=('GET','POST'))
@login_required
@verified_users
def home():

    form = CourseForm()
    delform = PhoneNumberForm()
    return render_template('home.html', exams=current_user.exams, form=form, delform=delform)

@app.route('/enroll',methods=('GET','POST'))
@login_required
@verified_users
def enroll():
    if not current_user.verified:
        return redirect(url_for('register'))

    form = CourseForm()
    if not form.validate_on_submit():
        flash("Invalid Course name provided", "warning")
        return redirect(url_for('home'))

    print(form.data['course'])
    course = Course.query.filter_by(name=form.data['course']).first()
    notif = Exam.query.filter_by(course = course, user= current_user).first()
    if course and not notif:
        exam = Exam.make_unique(course,DEFAULT_NOTIF,current_user)
        db.session.add(exam)
        db.session.commit()
        flash("You have successfully registered for this course.", "success")
    elif not course:
        flash("Course not found. Please enter the full course code as it appears on ACORN.", "warning")
    elif notif and course:
        flash("You are already registered in %s" % course.name, "warning")

    return redirect(url_for('home'))

@app.route('/unenroll/<course_code>',methods=('GET','POST'))
@login_required
@verified_users
def unenroll(course_code):

    if len(course_code) > 9 or len(course_code) < 6:
        flash("Invalid course code", "warning")
        return redirect(url_for('home'))

    course = Course.query.filter_by(name=course_code).first()
    notif = Exam.query.filter_by(course = course, user= current_user)
    if not course :
        flash("Course not found. Please screenshot this and scold francis because something is borked.","warning")
    elif not notif.all():
        flash("You are not registered in %s" % course.name, "warning")
    elif course and notif.all():
        notif.delete()
        db.session.commit()
        flash("You have been removed from the exam list.", "success")

    return redirect(url_for('home'))



@app.route('/delete', methods=('GET','POST'))
@login_required
@verified_users
def delete():
    form = PhoneNumberForm()
    if form.validate_on_submit():
        number = form.data['phone']
        print('Stored: %r  Provided: %r' % (current_user.phone,number))
        if number == current_user.phone:
            delete_user(current_user)
            flash("Your account has been deleted." , "success")
            return redirect(url_for('home'))

    flash("This is not your phone number. Deletion aborted.", "danger")
    return redirect(url_for('home'))


@app.route('/register',methods=('GET','POST'))
@login_required
def register():
    '''
    Checks to see if the user has verified their number (and redirects them away)
    :return: Forms to enter phone number, then token
    '''
    if current_user.verified:
        return redirect(url_for('home'))

    elif current_user.phone:
        token_form = TokenForm()
        if token_form.validate_on_submit():
            token = str(token_form.data['token'])
            if current_user.check_token(token):
                current_user.verified = True
                db.session.commit()
                return redirect(url_for('register'))
            else:
                flash('Please check your token.', "info")

        return render_template('token.html', form = token_form)
    else:
        form = PhoneNumberForm()
        if form.validate_on_submit():
            phoneNum = form.data['phone']
            if User.query.filter_by(phone = phoneNum, verified = True).all():
                flash("Number already in use.", "danger")
                return redirect(url_for('register'))
            current_user.phone = phoneNum
            update_token(current_user)                  #db committed in this method for us
            return current_user.token + " This is your token. Remember it or smth idc."
        return render_template('register.html', form=form)


@app.route('/resend')
@login_required
def resend_token():
    '''
    If the user has already verified their account, send them back to the homepage.
    '''
    if current_user.verified or not current_user.phone:
        return redirect(url_for('home'))

    delta = datetime.datetime.now() - current_user.token_date
    min_required = datetime.timedelta(minutes = 2)

    if min_required < delta:
        update_token(current_user)
        flash('A new token has been sent to %s' % current_user.phone, "success")
    else:
        flash('Please wait %s seconds before requesting a new token' % str((min_required-delta).seconds), "warning")

    flash('Your token is %s' % current_user.token)
    return redirect(url_for('register'))


@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')





if __name__ == '__main__':
    #make_users(db)
    #test_dup()
    #import_data()
    app.run(debug=True)