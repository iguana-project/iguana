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
from django.test.testcases import TestCase
import os

from common import settings, views
from django.contrib.auth import get_user_model


# currently only the avatars directory has an url config
testMediaFile = os.path.join(settings.MEDIA_ROOT, "avatars", "testFile")
testMediaUrl = os.path.join(settings.MEDIA_URL, "avatars", "testFile")
testMediaFileContent = "TestFile"


class ProtectedMediaDirTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify these elements they need to be created in setUp(), instead of here
        cls.user = get_user_model().objects.create_user("test", "test@test.de", "test1234")

        # create the media file for testing
        with open(testMediaFile, 'w') as f:
            f.write(testMediaFileContent)
            f.close()

    def setUp(self):
        self.client.force_login(self.user)
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()

    def test_view_and_template(self):
        # TODO TESTCASE common view and template
        #      use view_and_template()
        # TODO which views?
        #      - ShowProtectedFilesView - media/avatars - from a URL - should not deliver any content
        #      - ShowProtectedFilesView - media/avatars - from Django (by resolving a user page with an image)
        #                                                 should deliver the avatar
        #      - ShowProtectedFilesView - media/attachments - from a URL - should not deliver any content
        #      - ShowProtectedFilesView - media/attachments - from Django (accessing the attachment of an issue
        #                                                     from the issue detail page) - should deliver the content
        #      - CreateFilterView - ?
        #      - AutoCompleteView - ?
        #      - ...
        pass

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        # TODO TESTCASE common redirect to login and login required
        #      redirect_to_login_and_login_required()
        # TODO which views?
        #      - ShowProtectedFilesView - media/avatars
        #      - ShowProtectedFilesView - media/attachments
        #      - CreateFilterView - ?
        #      - AutoCompleteView - ?
        #      - ...
        pass

    @classmethod
    def tearDownClass(cls):
        # remove the media file again
        os.remove(testMediaFile)

        super(ProtectedMediaDirTest, cls).tearDownClass()

    def test_accesWithoutXAccel(self):
        views.USE_X_ACCEL_REDIRECT = False

        # get the file
        response = self.client.get(testMediaUrl)
        content = "".join([x.decode("utf-8") for x in response.streaming_content])

        self.assertEqual(testMediaFileContent, content)

    def test_accesWithXAccel(self):
        views.USE_X_ACCEL_REDIRECT = True

        # get the file
        response = self.client.get(testMediaUrl)
        accel = response["X-Accel-Redirect"]

        self.assertEqual(testMediaUrl, accel)

    def test_accesWithXAccelAndPrefix(self):
        views.USE_X_ACCEL_REDIRECT = True
        views.X_ACCEL_REDIRECT_PREFIX = "__prefix__"

        # get the file
        response = self.client.get(testMediaUrl)
        accel = response["X-Accel-Redirect"]

        self.assertEqual(os.path.join("/__prefix__", "avatars", "testFile"), accel)
