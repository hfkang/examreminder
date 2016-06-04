from .exams import Exam,User,Course,app, DEFAULT_NOTIF
from datetime import date

if __name__=='__main__':

    with app.test_request_context():
        today_eng = date.today().strftime('%b %d')
        today_eng = 'FRI 29 APR'
        today_artsci = date.today().strftime('%a %d %b').upper()


        exams_today = Course.query.filter_by(date = today).all()
        #notifications = Exam.query.filter_by(course.in_(exams_today)).all()
        notification_queue = []

        print(exams_today)
        for exam in exams_today:
            notification_queue.extend(Exam.query.filter_by(course = exam,notif = DEFAULT_NOTIF).all())
        print(notification_queue)

        for notification in notification_queue:
            print(notification.user.phone,notification.course.name,notification.course.time,notification.course.location)




