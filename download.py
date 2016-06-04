from bs4 import BeautifulSoup
import requests, pickle, datetime,sys,json,json_delta
from collections import defaultdict
from os import rename
from db_classes import Course, import_data, update_schedule

schedule_url = 'http://www.apsc.utoronto.ca/timetable/fes.aspx'
ARTSCI_SCHEDULE = 'http://www.artsci.utoronto.ca/current/exams/apr16'
PLACES_URL = 'http://www.artsci.utoronto.ca/current/exams/places'

def scrape():
    '''
    Download the schedule from the apsc website and scrape it into something useful.
    The method is currently hard coded to handle the apsc website, but bs4 can be used for the artsci calendar too.
    '''
    raw_page = requests.get(schedule_url).text
    #with open('fes.htm','r') as f:
    #    raw_page = f.read()
    soup = BeautifulSoup(raw_page,'html.parser')
    courses = soup.findAll('div',attrs = {'id':'logo'})

    exam_directory = {}

    for course in courses:

        exam = course.findChild()		#silly divtag
        code = exam.findChild()
        name = code.nextSibling
        typeDate = name.nextSibling.nextSibling
        time = typeDate.nextSibling.nextSibling

        typeAndDate = typeDate.split(',')

        rooms = [] #holds the array of which students go where
        room_assignments = course.findAll('tr',attrs = {'class': lambda a: "trx" in a or "trxc" in a})
        for cohort in room_assignments:
            cohort_info = cohort.findAll('td')
            cohort_name = cohort_info[1].text.strip()
            cohort_room = cohort_info[0].text.strip().replace('-',' ')
            cohort_msg	= cohort_info[2].text.strip()

            rooms.append([cohort_name,cohort_room,cohort_msg])

        exam_directory[code.text.strip()] = {'name':name.strip(),
                                             'type':typeAndDate[0].strip(),
                                             'date':typeAndDate[1].strip()[6:],
                                             'time':time.strip()[5:],
                                             'rooms':rooms}


    #with open('examsched.pickle','wb') as f:
    #pickle.dump(exam_directory, f)
    rename('examsched.json','prevexamsched.json')

    with open('examsched.json','w') as f:
        json.dump(exam_directory,f)


def scrape_artsci():
    '''
    Scrapes the artsci examination timetable and stores it as a json file (this is so we can generate diffs)
    Table follows following structure:
    (Course 	Section 	Date 	Time 	Location)
    :return:
    :saves: artsci_sched.json
    '''

    raw_page = requests.get(ARTSCI_SCHEDULE).text
    soup = BeautifulSoup(raw_page,'html.parser')

    courses = soup.find('table',attrs = {'class':'vertical listing'})       # Grab exam timetable
    # Remove nbsp artifacts from the html, and any trailing whitespace
    exam_table = [[cell.text.replace('\u00a0','').strip()\
                   for cell in row('td')] for row in courses('tr')[1:]]     # Convert html table into 2D array
    # Convert the timetable into dictionary where key: course code, and value: list of data [(section,date,time,location)]
    exam_dict = defaultdict(list)
    for exam in exam_table:
        exam_dict[exam[0]].append(exam[1:])


    # Archive data as json files
    rename('artsci_sched.json','prev_artsci_sched.json')
    with open('artsci_sched.json', 'w') as f:
        json.dump(exam_dict,f)


def scrape_locations():
    '''
    This method needs to be called very seldome and can be done manually.
    It downloads the building shortcodes used by the university in examinations
    :return:
    '''

    raw_page = requests.get(PLACES_URL).text
    soup = BeautifulSoup(raw_page,'html.parser')

    buildings = soup.find('table',attrs = {'class':'vertical listing'})      # Grab exam timetable
    building_table = [[' '.join(cell.text.replace('\u2019', '').strip().split() )\
                   for cell in row('td')] for row in buildings('tr')[1:]]  # Convert html table into 2D array

    for row in building_table:
        row.append(row[1])

    with open('buildings.json','w') as f:
        json.dump(building_table,f)

def track_changes():
    '''Calculates the diff between the two schedules.
    This method is to be called on a regular (daily) basis, and will be used to notify users of any changes to their exams
    '''
    with open('examsched.json','r') as f:
        current = json.load(f)
    with open('prevexamsched.json','r') as f:
        old = json.load(f)
    with open('artsci_sched.json','r') as f:
        current_artsci = json.load(f)
    with open('prev_artsci_sched.json','r') as f:
        old_artsci = json.load(f)

    current.update(current_artsci)
    old.update(old_artsci)

    tags = ('time','date','rooms')
    schedule_changes = defaultdict(list)			#key: coursecode . List of tag changes made to each course

    delta = json_delta.diff(old, current, minimal=True, verbose=True, key=None )
    for diff in delta:
        course_code = diff[0][0]		#Course code in diff structure
        changed = diff[0][1]			#tag that changed in the exam schedul
        schedule_changes[course_code].append(changed)

    for change in list(schedule_changes.items()):
        schedule_changes[change[0]] = list(set(change[1]))		#remove duplicate entries of changed elements for each course

    with open('changes.json','w') as f:
        json.dump(schedule_changes,f)

def package_json(exams):
    '''
    Takes in the dictionary of exams and exports the keys as a json list to exams_list.json
    This is so that the frontend can have a list of exams tracked by the system for when users enroll in a course.
    :param exams:
    :return: none
    '''
    min_dict = [course.name for course in exams]

    with open('static/exams_list.json','w') as f:
        json.dump(min_dict,f)

def scrape_all_and_save():

    scrape()                #Download and scrape engineering schedule and place in examsched.json
    scrape_artsci()         #Download and scrape artsci schedule and place in artsci_sched.json

    from exams import app
    with app.test_request_context():
        import_data()
        package_json(Course.query.all())                                #Export course names to json array for frontend
        print(Course.query.filter_by(name='ACT470H1S').first())
        print(Course.query.filter_by(name='MIE210H1').first())
        track_changes()
        update_schedule()

if __name__ == "__main__":
    scrape_all_and_save()