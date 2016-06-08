import sys,os
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/roomplz')
from exams import app as exrem
from hello import app as roomplz
from admin import app as adminapp
from werkzeug.wsgi import DispatcherMiddleware

os.chdir('/app/roomplz')

application = DispatcherMiddleware(roomplz, {'/remind':exrem, '/admin':adminapp})
