"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
import datetime

from common.validators import date_is_present_or_future


class ValidatorTest(TestCase):
    def test_validation(self):
        # valid test objects
        valid_testobjs = {
            'date-today': datetime.date.today(),
            'date-future': datetime.date.today() + datetime.timedelta(days=1),
            'datetime-future': datetime.datetime.today() + datetime.timedelta(days=1),
        }

        for obj in valid_testobjs:
            date_is_present_or_future(valid_testobjs[obj])

        invalid_testobjs = {
            'date-yesterday': datetime.date.today() - datetime.timedelta(days=1),
            'datetime-yesterday': datetime.datetime.today() - datetime.timedelta(days=1),
            'invalid-object': self,
        }

        for obj in invalid_testobjs:
            self.assertRaises(ValidationError, date_is_present_or_future, invalid_testobjs[obj])
