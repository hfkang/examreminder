import unittest
import config as c
from datetime import datetime
from download import get_semester, get_building

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


    def test_fall_semester(self):
        fall = datetime(2016, 11, 25)
        assert get_semester(fall) == ('dec','16')

    def test_summer_semester(self):
        summer = datetime(2015, 6, 20)
        assert get_semester(summer) == ('june','15')

    def test_winter_semseter(self):
        winter = datetime(2014, 2, 10)
        assert get_semester(winter) == ('apr','14')

    def test_get_building_exam_center(self):
        assert get_building('EX 200', building_list) == 'EX'

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