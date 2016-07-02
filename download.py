from bs4 import BeautifulSoup
import requests, datetime,sys, json, json_delta
from collections import defaultdict
from os import rename, path
import re
import config as c


def get_semester(datetime):
    # I overwrite variables with another type because I'm rebelling against python's absurd type system
    month = datetime.month
    if month in range(5):
        month = 'apr'
    elif month in range(5, 8):
        month = 'june'
    elif month in range(8, 11):
        month = 'aug'
    elif month in range(11, 13):
        month = 'dec'
    else:
        month = 'apr'
    year = str(datetime.year)[2:]
    return month,year


def get_building(room,building_list):
    regex = re.compile(room.split()[0])
    for building in building_list:
        if regex.match(building):
            print(room,building)
            return building


def archive_data(current_file,prev_file,exam_dict):
    if path.isfile(current_file):
        rename(current_file,prev_file)
    else:
        # Create empty previous file so json_delta has something to look at and can generate properly formed diff stanza
        with open(prev_file,'w') as f:
            json.dump({}, f)

    with open(current_file, 'w') as f:
        json.dump(exam_dict,f)


def scrape_engineering():
    '''
    Download the schedule from the apsc website and scrape it into something useful.
    The method is currently hard coded to handle the apsc website, but bs4 can be used for the artsci calendar too.
    '''
    raw_page = requests.get(c.eng_url).text
    soup = BeautifulSoup(raw_page,'html.parser')
    courses = soup.findAll('div',attrs = {'id':'logo'})

    exam_directory = {}

    with open(c.buildings_file,'r') as f:
        building_list = json.load(f)

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
            cohort_building = get_building(cohort_room,building_list)
            rooms.append([cohort_name,cohort_room,cohort_building])

        date = typeAndDate[1].strip()[6:]
        time = time.strip()[5:]
        faculty = 'eng'
        ex_type = typeAndDate[0].strip()

        exam_directory[code.text.strip()] = [rooms,date,time,faculty,ex_type]

    archive_data(c.current_eng_sched, c.prev_eng_sched, exam_directory)

def ingest_artsci(exam,exam_dict,buildings):
    '''
    Helper function to convert artsci dictionary format into desired format shared by engineering timetable
    :param exam: course code to be scraped
    :param exam_dict: source dictionary obtained from scraping
    :param buildings: buildings.json dict passed in from parent function
    :return: date,time,rooms (json'd)
    '''
    exam_data = exam_dict[exam][0]
    time = exam_data[2][:7].replace("EV", "PM")
    # Artsci calendar has format (DAY DD MON) Convert to engineering format (MON DD)
    # It also stores the time like PM 2:00 , and seems to have start times of 9am, 2pm, and 7pm only
    date_obj = datetime.datetime.strptime(exam_data[1] + time, '%a %d %b%p %I:%M')
    date = date_obj.strftime('%b %d')
    time = date_obj.strftime('%I:%M %p')
    rooms = [[section[0], section[3],get_building(section[3],buildings)] for section in exam_dict[exam]]

    return date,time,rooms


def scrape_artsci():
    '''
    Scrapes the artsci examination timetable and stores it as a json file (this is so we can generate diffs)
    Table follows following structure:
    (Course 	Section 	Date 	Time 	Location)
    :return:
    :saves: artsci_sched.json
    '''

    month,year = get_semester(datetime.datetime.now())
    url =c.artsci_url + month + year

    raw_page = requests.get(url).text
    soup = BeautifulSoup(raw_page,'html.parser')

    courses = soup.find('table',attrs = {'class':'vertical listing'})       # Grab exam timetable
    # Remove nbsp artifacts from the html, and any trailing whitespace
    exam_table = [[cell.text.strip()\
                   for cell in row('td')] for row in courses('tr')[1:]]     # Convert html table into 2D array
    # Convert the timetable into dictionary where key: course code, and value: list of data [(section,date,time,location)]
    exam_dict = defaultdict(list)   #temporary dictionary to store data, have it processed by ingest_artsci
    for exam in exam_table:
        exam_dict[exam[0]].append(exam[1:])

    faculty = 'artsci'
    exam_type = 'na'

    #Open file outside of main loop so we don't load the same thing over and over
    with open(c.buildings_file,'r') as f:
        buildings = json.load(f)

    exam_dict_export = {}
    for exam in exam_dict:
        date, time, rooms = ingest_artsci(exam,exam_dict,buildings)
        exam_dict_export[exam] = [rooms,date,time,faculty,exam_type]

    archive_data(c.current_artsci_sched, c.prev_artsci_sched, exam_dict_export)


def scrape_locations():
    '''
    This method is kept for archival purposes. It was used to download the buildings.json file, and was
    manually edited so that addresses would resolve in google maps. It should no longer be used unless the university
     adds new buildings.
    :return: nothing. but it saves the schedule in the data directory
    '''
    raw_page = requests.get(c.buildings_url).text
    soup = BeautifulSoup(raw_page,'html.parser')

    buildings = soup.find('table',attrs = {'class':'vertical listing'})      # Grab exam timetable
    building_table = [[' '.join(cell.text.replace('\u2019', '').strip().split() )\
                   for cell in row('td')] for row in buildings('tr')[1:]]  # Convert html table into 2D array

    for row in building_table:
        row.append(row[1])

    with open(c.buildings_file,'w') as f:
        json.dump(building_table,f)

def track_changes():
    '''Calculates the diff between the two schedules.
    This method is to be called on a regular (daily) basis, and will be used to notify users of any changes to their exams
    This is also is used to update the database, as it informs the system of any courses that have changed, or new courses
    In the event of a course being deleted from the schedule for some reason, the system will just send an update that
    the course has changed something. Anything beyond that is beyond the scope of this application
    '''
    with open(c.current_eng_sched,'r') as f:
        current = json.load(f)
    with open(c.prev_eng_sched,'r') as f:
        old = json.load(f)

    with open(c.current_artsci_sched,'r') as f:
        current_artsci = json.load(f)
    with open(c.prev_artsci_sched,'r') as f:
        old_artsci = json.load(f)

    current.update(current_artsci)
    old.update(old_artsci)

    schedule_changes = []			    #List of courses to update

    delta = json_delta.diff(old, current, verbose=True, key=None )
    #print(delta)
    if delta and len(delta[0]) > 1 and not delta[0][0]:
        # [[[],<target>]] format generated by json_delta. prepare the cannons for mass updates!
        schedule_changes = list(delta[0][1].keys())
    else:
        for course in delta:
            schedule_changes.append(course[0][0])

    #print(schedule_changes)

    schedule_changes= list(set(schedule_changes))		#remove duplicate entries of changed elements for each course
    with open(c.delta_file,'w') as f:
        json.dump(schedule_changes,f)

    package_json(current)              #generate minimized list of courses for consumption by frontend

def package_json(exams):
    '''
    Takes in the dictionary of exams and exports the keys as a json list to exams_list.json
    This is so that the frontend can have a list of exams tracked by the system for when users enroll in a course.
    :param exams:
    :return: none
    '''
    min_dict = list(exams.keys())

    with open(c.packaged_courses,'w') as f:
        json.dump(min_dict,f)

def scrape_all_and_save():
    scrape_engineering()                #Download and scrape engineering schedule and place in examsched.json
    scrape_artsci()         #Download and scrape artsci schedule and place in artsci_sched.json
    track_changes()         #Get diff, and package json file while you're at it




if __name__ == "__main__":
    scrape_all_and_save()