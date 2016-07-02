import unittest
import config as c
from datetime import datetime
from download import get_semester, get_building, archive_data
import uuid
import os
import json

building_list = {
    "EX": ["Central Exams Facility, 255 McCaul St. (just south of College St.)", "255 McCaul St."],
    "IN": ["Innis College, 2 Sussex Avenue (IN112 is Innis Town Hall)", "2 Sussex Avenue"],
    "WB": ["Wallberg Building,184-200 College Street", "200 College Street"],
    "BN 3": ["Upper Small Gymnasium, Benson Building, 320 Huron Street (south of Harbord Street), Third Floor",
             "Benson Building, 320 Huron Street"],
    "HI CART": ["Cartwright Hall, St. Hilda's College, 44 Devonshire Place", "44 Devonshire Place"],
    "BA": ["Bahen Centre for Information Technology, 40 St. George Street",
           "Bahen Centre for Information Technology, 40 St. George Street"]
}


class DownloaderTester(unittest.TestCase):

    @staticmethod
    def create_current_file():
        current = str(uuid.uuid4())
        testinfo = "right✔there ✔✔if i do ƽaү so my self 💯 i say so 💯 thats what im talking about right there right there"
        with open(current,'w') as f:
            f.write(testinfo)
        return current,testinfo

    def test_file_gets_renamed_with_empty_data(self):
        current,testinfo = self.create_current_file()
        previous = str(uuid.uuid4())
        archive_data(current,previous,{})
        with open(previous,'r') as f:
            assert f.read() == testinfo

        os.remove(current)
        os.remove(previous)

    def test_file_is_created_if_no_current_with_empty_data(self):
        current = str(uuid.uuid4())
        previous = str(uuid.uuid4())
        archive_data(current,previous,{})
        with open(previous,'r') as f:
            assert f.read() == json.dumps({})

        os.remove(current)
        os.remove(previous)

    def test_file_is_renamed_with_some_data(self):
        current,testinfo = self.create_current_file()
        previous = str(uuid.uuid4())
        archive_data(current,previous,{"HI":"BYE"})
        with open(current,'r') as f:
            assert f.read() == json.dumps({"HI":"BYE"})

        os.remove(current)
        os.remove(previous)



    def test_fall_semester(self):
        fall = datetime(2016, 11, 25)
        assert get_semester(fall) == ('dec','16')

    def test_fall_semester_in_december(self):
        fall = datetime(2016, 12, 25)
        assert get_semester(fall) == ('dec','16')

    def test_summer_semester(self):
        summer = datetime(2015, 6, 20)
        assert get_semester(summer) == ('june','15')

    def test_summer_semester_june_again(self):
        summer = datetime(2015, 7, 20)
        assert get_semester(summer) == ('june','15')

    def test_summer_calendar_gets_august(self):
        august = datetime(2013, 8, 29)
        assert get_semester(august) == ('aug', '13')

    def test_summer_calendar_gets_august_in_september(self):
        august = datetime(2013, 9, 15)
        assert get_semester(august) == ('aug', '13')

    def test_summer_calendar_gets_august_in_october(self):
        august = datetime(2013, 10, 29)
        assert get_semester(august) == ('aug', '13')

    def test_winter_semseter(self):
        winter = datetime(2014, 2, 10)
        assert get_semester(winter) == ('apr','14')

    def test_winter_semseter_march(self):
        winter = datetime(2014, 3, 10)
        assert get_semester(winter) == ('apr', '14')

    def test_winter_semseter_april(self):
        winter = datetime(2014, 4, 10)
        assert get_semester(winter) == ('apr', '14')



    def test_get_building_exam_center(self):
        assert get_building('EX 200', building_list) == 'EX'

    def test_get_building_walberg(self):
        assert get_building('WB sdfw23', building_list) == 'WB'

    def test_get_building_exam_center_wrong(self):
        assert get_building('EX100', building_list) == None

    def test_get_building_exam_center_extra(self):
        assert get_building('EX 200, WB 2000', building_list) == 'EX'

    def test_get_building_HI_CART(self):
        assert get_building('HI CART ROOM', building_list) == 'HI CART'

    def test_get_building_garbage(self):
        assert get_building('not a room', building_list) == None

if __name__ == '__main__':
    unittest.main()