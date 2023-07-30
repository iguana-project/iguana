"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin, Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under BSD-2-Clause License.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
   2. Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer
      in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from django.db import IntegrityError


class LoginTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
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
