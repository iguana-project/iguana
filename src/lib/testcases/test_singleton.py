"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import TestCase
from lib.singleton import Singleton


class SimpleSingleton(Singleton):
    pass


class TestSingleton(TestCase):
    def test_singleton(self):
        obj1 = SimpleSingleton.instance
        obj2 = SimpleSingleton.instance
        self.assertEqual(obj1, obj2)
        self.assertEqual(id(obj1), id(obj2))
