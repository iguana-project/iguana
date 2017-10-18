"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from django.db import IntegrityError


class LoginTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')

    def test_preferences(self):
        user = self.user

        # assert that we have no preferences
        self.assertEqual(user.preferences.count(), 0)

        self.assertEqual(user.get_preference('a'), None)
        self.assertEqual(user.get_preference('a', 'default'), 'default')
        self.assertEqual(user.preferences.count(), 0)

        # add new preference
        user.set_preference('a', 'b')
        self.assertEqual(user.preferences.count(), 1)
        self.assertEqual(user.get_preference('a'), 'b')
        self.assertEqual(user.get_preference('a', 'default'), 'b')

        # add another preference
        user.set_preference('b', 'b')
        self.assertEqual(user.preferences.count(), 2)
        self.assertEqual(user.get_preference('a'), 'b')
        self.assertEqual(user.get_preference('b'), 'b')
        self.assertEqual(user.get_preference('b', 'default'), 'b')

        # overwrite first preference
        user.set_preference('a', 'c')
        self.assertEqual(user.preferences.count(), 2)
        self.assertEqual(user.get_preference('a'), 'c')
        self.assertEqual(user.get_preference('b'), 'b')

        # try to add None value (should lead to key deletion)
        user.set_preference(key='a', value=None)
        self.assertEqual(user.preferences.count(), 1)
        self.assertEqual(user.get_preference('a'), None)
        self.assertEqual(user.get_preference('a', 'default'), 'default')
