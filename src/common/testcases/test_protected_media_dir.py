"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
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
        # NOTE: if you modify this element it needs to be created in setUp, instead of here
        cls.user = get_user_model().objects.create_user("test", "test@test.de", "test1234")

        # create the media file for testing
        with open(testMediaFile, 'w') as f:
            f.write(testMediaFileContent)
            f.close()

    def setUp(self):
        self.client.force_login(self.user)

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

        self.assertEqual("/__prefix__" + testMediaUrl, accel)
