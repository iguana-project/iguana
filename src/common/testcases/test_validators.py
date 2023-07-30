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
