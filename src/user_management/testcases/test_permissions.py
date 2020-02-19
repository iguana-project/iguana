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


class PermissionsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user('a', 'b', 'c')
        cls.user2 = get_user_model().objects.create_user('d', 'e', 'f')

    def setUp(self):
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        pass

    def test_permissions(self):
        user = self.user

        self.assertEqual(user.user_has_read_permissions(self.user), True)
        self.assertEqual(user.user_has_read_permissions(self.user2), True)

        self.assertEqual(user.user_has_write_permissions(self.user), True)
        self.assertEqual(user.user_has_write_permissions(self.user2), False)
