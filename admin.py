from flask import Flask, redirect, url_for, session, request,render_template,flash, abort
from flask_login import UserMixin
from flask_oauthlib.client import OAuth, OAuthException
from flask_login import LoginManager, login_user ,current_user,login_required, logout_user
from forms import TableManageForm
from functools import wraps
import subprocess
from db_classes import Course, Exam, User, db, reset_table, update_schedule
from download import scrape_artsci, scrape_engineering

app = Flask(__name__)
app.config.from_pyfile('config.py')     #set as envar in local windows environment.
# This doesn't seem to be specified by the werkzeug dispatcher middleware, and is necessary to prevent cookie clash
app.config['APPLICATION_ROOT'] = '/admin'
db.init_app(app)

oauth = OAuth()
oauth.init_app(app)

lm = LoginManager(app)
lm.login_view= 'login'

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



def admin_only(func):
    @wraps(func)
    def verify(*args,**kwargs):
        if not current_user.social_id == app.config['ADMIN_ID']:
            return redirect(url_for('login',_external=True))
        return func(*args,**kwargs)
    return verify

@lm.user_loader
def load_user(id):
    return AdminUser(id)

@app.route('/')
@login_required
@admin_only
def admin():
    return render_template('admin.html')


@app.route('/payload', methods=['POST'])
def payload():
    '''
    Endpoint for Github webhook. Used for deployments
    Set repo_path and the wsgi_app entry point in app config
    :return:
    '''
    exit = subprocess.run(['git','pull --recurse-submodules'], cwd=app.config['REPO_PATH'],stdout=subprocess.PIPE)
    if exit.returncode != 0:
        return exit.stdout, 500
    # Actually update roomplz
    exit = subprocess.run(['git','submodule update --recursive'],cwd=app.config['REPO_PATH'],stdout=subprocess.PIPE)
    if exit.returncode != 0:
        return exit.stdout, 500
    exit = subprocess.run(['touch','wsgi_app.py'],cwd=app.config['REPO_PATH'])
    if exit.returncode != 0:
        return "failed wsgi application update",500
    return "Update successful!",200


@app.route('/users')
@login_required
@admin_only
def edit_user():
    return render_template('edit_user.html')

@app.route('/roomplz')
@admin_only
def roomplz():
    return render_template('admin_roomplz.html')

@app.route('/osm')
@admin_only
def osm():
    exit = subprocess.run(['python','osm.py','--all'], cwd="roomplz",stdout=subprocess.PIPE)
    if exit.returncode != 0:
        return exit.stdout, 500

    return exit.stdout

@app.route('/logs')
@login_required
@admin_only
def logs():
    errorlogs = open('logs/error.log').read()
    errorlogs.replace('\n','<br>')
    accesslogs = open('logs/access.log').read()
    accesslogs.replace('\n','<br>')

    return render_template('admin_logs.html',elogs=errorlogs,alogs=accesslogs)

@app.route('/tables')
@login_required
@admin_only
def admin_tables():
    course_table = Course.query.all()
    user_table = User.query.all()
    exams = Exam.query.all()
    return render_template('admin_tables.html', user_table=user_table,course_table=course_table,exam_table=exams)

@app.route('/tables/manage',methods=['GET','POST'])
@login_required
@admin_only
def tables_manage():
    form = TableManageForm()
    if form.validate_on_submit():
        table = form.table.data
        action = form.action.data
        if action == 'Reset':
            if table == 'User':
                drop = User
            elif table == 'Course':
                drop = Course
            elif table == 'Exam':
                drop = Exam
            if drop:
                reset_table(drop)
            flash('%s table has been DROPPED'%table,'success')

        elif table == 'Course':
            eng = form.engineering.data
            artsci = form.artsci.data
            if action == 'Scrape':
                if eng:
                    flash('We are going to scrape the Engineering calendar', 'info')
                    scrape_engineering()
                if artsci:
                    flash('Scraped the artsci cal from: %s' % app.config['ARTSCI_URL'], 'info')
                    scrape_artsci()
            elif action == 'Update':
                flash('Going to update from eng: %s and artsci: %s'%(eng,artsci), 'info')
                update_schedule(useArtsci=artsci,useEngsci=eng)

    elif request.method == 'POST':
        flash('Wrong token or smth. Check your form!','danger')
        print(form.errors)

    return render_template('admin_tables_manage.html', form=form, token="asdf1")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return "You've been logged out :-)"

@app.route('/login')
def login():
    callback = url_for('authorized',_external = True)
    return google.authorize(callback=callback)

@app.route('/login/authorized')
def authorized():
    resp = google.authorized_response()

    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )


    if resp is None:
        abort(401)

    if isinstance(resp, OAuthException):
        abort(418)

    session['google_token'] = (resp['access_token'], '')
    me = google.get('userinfo')
    social_id = me.data['id']

    if social_id is None:
        flash('Authentication failed.')
        abort(401)

    user = AdminUser(social_id)

    if social_id == app.config['ADMIN_ID']:
        login_user(user, True)
        return redirect(url_for('admin',_external = True))        #home is for logged in users

    abort(401)

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

class AdminUser(UserMixin):
    def __init__(self,id):
        self.social_id = id
        self.id = id

if __name__ == '__main__':
    app.run(debug=True)