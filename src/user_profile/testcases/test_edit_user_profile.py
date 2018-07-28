"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test.testcases import TestCase
from django.urls.base import reverse
from django.core.files.uploadedfile import SimpleUploadedFile, UploadedFile
from io import BytesIO
import os
from PIL import Image
import shutil

from common.settings import BASE_DIR, MEDIA_ROOT
from user_profile.apps import defaultAvatar
from django.contrib.auth import get_user_model

from user_management.views import LoginView
from user_profile.views import EditProfilePageView

user_name = "user_name"
test_password = "test1234"
test_new_password = "new_pass4321"
test_email = "test@testing.com"
first_name = "firstabc"
last_name = "Default-def"
timezone = "Europe/Berlin"

second_user_name = "test2"
second_user_password = "test21234"
second_user_email = "test2@testing.com"

no_image_byte_code = b'no_image'
image_path = os.path.join(os.path.dirname(BASE_DIR), "user_profile/testcases/test_image.png")
file_path_png = os.path.join(MEDIA_ROOT, "avatars", user_name, "file.png")
uploaded_image_path = os.path.join(MEDIA_ROOT, "avatars", user_name, "test_image.png")

default_dict = {
    'email': test_email,
    'first_name': first_name,
    'last_name': last_name,
    'language': 'en',
    'timezone': timezone
}
default_dict2 = {
    'email': test_email,
    'avatar': '',
    'timezone': timezone,
    'language': 'en',
}
random_pw = "wajdpoiwajpod_this_is_totally_random_equal_wajdpoiwajpod"

error_incorrect_old = "Your old password was entered incorrectly. Please enter it again."
error_short_new = "This password is too short. It must contain at least 8 characters."
error_didnt_match = "The two password fields didn&#39;t match."
error_either_didnt_match_or = "Either the two password fields didn&#39;t " \
                              "match or additional restrictions are not fullfilled."
error_too_similar_to = "The password is too similar to "

edit_template = 'user_profile/edit_user_profile.html'
user_template = 'user_profile/user_profile_page.html'


class EditUserProfileTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # NOTE: if you modify this element it needs to be created in setUp, instead of here
        cls.user2 = get_user_model().objects.create_user(second_user_name, second_user_email,
                                                         second_user_password)
        cls.removeTestImagePath()

    @classmethod
    def tearDownClass(cls):
        cls.removeTestImagePath()
        super(EditUserProfileTest, cls).tearDownClass()

    @classmethod
    def removeTestImagePath(cls):
        # clear the test user avatar directory
        testAvatarDir = os.path.dirname(uploaded_image_path)
        shutil.rmtree(testAvatarDir, ignore_errors=True)

    def setUp(self):
        # NOTE: this element gets modified by some of those tests, so this shall NOT be created in setUpTestData()
        self.user = get_user_model().objects.create_user(user_name, test_email, test_password)
        self.client.force_login(self.user)

    def tearDown(self):
        if os.path.isfile(file_path_png):
            os.remove(file_path_png)

    def test_view_and_template(self):
        response = self.client.get(reverse('user_profile:edit_profile', kwargs={"username": user_name}), follow=True)
        self.assertTemplateUsed(response, edit_template)
        self.assertEqual(response.resolver_match.func.__name__, EditProfilePageView.as_view().__name__)

    def test_redirect_to_login_and_login_required(self):
        self.client.logout()
        response = self.client.get(reverse('user_profile:edit_profile', kwargs={"username": user_name}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/login/?next=' + reverse('user_profile:edit_profile',
                                                                         kwargs={'username': user_name}))

    def test_other_user_edit_page_not_accassible_user_passes_test_mixin(self):
        self.client.logout()
        self.client.force_login(self.user2)
        response = self.client.get(reverse('user_profile:edit_profile', kwargs={"username": user_name}))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['location'], '/login/?next=' + reverse('user_profile:edit_profile',
                                                                         kwargs={'username': user_name}))

    def test_show_own_user_edit_page(self):
        response = self.client.get(reverse('user_profile:edit_profile', kwargs={"username": user_name}))
        self.assertEqual(response.status_code, 200)

    def test_edit_page_with_get_request_disabled(self):
        pass_dict = {'old_password': test_password, 'new_password1': test_new_password,
                     'new_password2': test_new_password}
        response = self.client.get(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                   pass_dict)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # zero elements in change password => other form is used not change pw
    #                                  => success => redirect to user, without changing pw
    def test_change_user_profile(self):
        response = self.client.post(reverse('user_profile:edit_profile',
                                    kwargs={"username": user_name}), default_dict, follow=True)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    def test_upload_avatar_inTemp(self):
        avatar = open(image_path, "rb")
        new_dict = default_dict2.copy()
        new_dict['avatar'] = avatar
        avatar2 = UploadedFile(avatar, name=avatar.name, content_type="image/png", size=os.path.getsize(image_path))
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    new_dict, follow=True)
        self.assertContains(response, avatar2)
        self.delete_image_test()
        avatar.close()

    # helper function
    def delete_image_test(self):
        new_dict = default_dict2.copy()
        new_dict['avatar-clear'] = True
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    new_dict, follow=True)
        self.assertFalse(os.path.exists(uploaded_image_path))
        self.assertIn(defaultAvatar, response.content.decode(response.charset))

    def test_upload_avatar_inMem(self):
        i = Image.new("RGB", (1, 1), "white")
        output = BytesIO()
        i.save(output, format="PNG")
        output.flush()
        output.seek(0)

        avatar = SimpleUploadedFile("file.png", content=output.getvalue(), content_type="image/png")
        avatar.file.seek(0)
        new_dict = default_dict2.copy()
        new_dict['avatar'] = avatar
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    new_dict, follow=True)
        self.assertContains(response, avatar)

    def test_upload_not_an_image(self):
        avatar = SimpleUploadedFile("file.png", content=no_image_byte_code, content_type="image/png")
        avatar.file.seek(0)
        new_dict = default_dict2.copy()
        new_dict['avatar'] = avatar
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    new_dict, follow=True)
        self.assertTrue("not an image or a corrupted image" in str(response.content))

    # change password tests NOTE: it is pretty important to do all those tests, because the code is very case dependent
    # the numers (one, two, three) show how many of those pw-fields are filled
    # one element: wrong old pw => error => "Your old password was entered incorrectly. Please enter it again."
    def test_ch_pw_one_wrong_old(self):
        new_dict = default_dict.copy()
        new_dict['old_password'] = test_password+"this_is_wrong_now"
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}), new_dict)
        self.assertContains(response, error_incorrect_old)
        self.assertNotContains(response, error_didnt_match)
        self.assertNotContains(response, error_either_didnt_match_or)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # one element: correct old pw => success => redirect to user, without changing pw
    def test_ch_pw_one_correct_old(self):
        new_dict = default_dict.copy()
        new_dict['old_password'] = test_password
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    new_dict, follow=True)
        # check used template
        self.assertTemplateUsed(response, user_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # one element: new_pw1 => error => "Your old password was entered incorrectly. Please enter it again."
    #                               => "This password is too short. It must contain at least 8 characters."
    def test_ch_pw_one_pw1(self):
        new_dict = default_dict.copy()
        new_dict['new_password1'] = random_pw
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}), new_dict)
        self.assertContains(response, error_incorrect_old)
        self.assertContains(response, error_short_new)
        self.assertNotContains(response, error_didnt_match)
        self.assertNotContains(response, error_either_didnt_match_or)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # one element: new_pw2 => error => "The two password fields didn't match."
    def test_ch_pw_one_pw2(self):
        new_dict = default_dict.copy()
        new_dict['new_password2'] = random_pw
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}), new_dict)
        self.assertContains(response, error_didnt_match)
        self.assertNotContains(response, error_either_didnt_match_or)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # two elements: new_pw1, new_pw2 (different) => error =>
    #                                            => "Your old password was entered incorrectly. Please enter it again."
    #                                            => "The two password fields didn't match."
    def test_ch_pw_two_pw1_pw2_different(self):
        new_dict = default_dict.copy()
        new_dict['new_password1'] = "this_is_totally_random_first_one"
        new_dict['new_password2'] = "this_is_totally_random_second_one_and_different"
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}), new_dict)
        self.assertContains(response, error_incorrect_old)
        self.assertContains(response, error_didnt_match)
        self.assertNotContains(response, error_either_didnt_match_or)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # two elements: new_pw1, new_pw2 (equal) => error =>
    #                                        => "Your old password was entered incorrectly. Please enter it again."
    def test_ch_pw_two_pw1_pw2_equal(self):
        new_dict = default_dict.copy()
        new_dict['new_password1'] = random_pw
        new_dict['new_password2'] = random_pw
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}), new_dict)
        self.assertContains(response, error_incorrect_old)
        self.assertNotContains(response, error_didnt_match)
        self.assertNotContains(response, error_either_didnt_match_or)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # two elements: wrong old, new_pw1 => error => "Your old password was entered incorrectly. Please enter it again."
    #                                           => "This password is too short. It must contain at least 8 characters."
    def test_ch_pw_two_wrong_old_pw1(self):
        new_dict = default_dict.copy()
        new_dict['old_password'] = test_password+"this_is_wrong_now"
        new_dict['new_password1'] = random_pw
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}), new_dict)
        self.assertContains(response, error_incorrect_old)
        self.assertContains(response, error_short_new)
        self.assertNotContains(response, error_didnt_match)
        self.assertNotContains(response, error_either_didnt_match_or)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # two elements: wrong old, new_pw2 => error => "Your old password was entered incorrectly. Please enter it again."
    #                                           => "The two password fields didn't match."
    def test_ch_pw_two_wrong_old_pw2(self):
        new_dict = default_dict.copy()
        new_dict['old_password'] = test_password+"this_is_wrong_now"
        new_dict['new_password2'] = random_pw
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}), new_dict)
        self.assertContains(response, error_incorrect_old)
        self.assertContains(response, error_didnt_match)
        self.assertNotContains(response, error_either_didnt_match_or)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # two elements: correct old, new_pw1 => error => "The two password fields didn't match."
    #               => "Either the two password fields didn&#39;t match or additional restrictions are not fullfilled."
    def test_ch_pw_two_correct_old_pw1(self):
        new_dict = default_dict.copy()
        new_dict['old_password'] = test_password
        new_dict['new_password1'] = random_pw
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}), new_dict)
        self.assertContains(response, error_short_new)
        self.assertContains(response, error_either_didnt_match_or)
        self.assertNotContains(response, error_didnt_match)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # two elements: correct old, new_pw2 => error => "The two password fields didn't match."
    def test_ch_pw_two_correct_old_pw2(self):
        new_dict = default_dict.copy()
        new_dict['old_password'] = test_password
        new_dict['new_password2'] = random_pw
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}), new_dict)
        self.assertContains(response, error_didnt_match)
        self.assertNotContains(response, error_either_didnt_match_or)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # three elements: wrong old, new_pw1, new_pw2 (different) => error => "The two password fields didn't match."
    #                                      => "Your old password was entered incorrectly. Please enter it again."
    def test_ch_pw_three_wrong_old_pw_1_pw2_different(self):
        new_dict = default_dict.copy()
        new_dict['old_password'] = test_password+"this_is_wrong_now"
        new_dict['new_password1'] = "this_is_totally_random_first_one"
        new_dict['new_password2'] = "this_is_totally_random_second_one_and_different"
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}), new_dict)
        self.assertContains(response, error_didnt_match)
        self.assertContains(response, error_incorrect_old)
        self.assertNotContains(response, error_either_didnt_match_or)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # three elements: correct old, new_pw1, new_pw2 (different) => error => "The two password fields didn't match."
    #               => "Either the two password fields didn&#39;t match or additional restrictions are not fullfilled."
    def test_ch_pw_three_correct_old_pw_1_pw2_different(self):
        new_dict = default_dict.copy()
        new_dict['old_password'] = test_password
        new_dict['new_password1'] = "this_is_totally_random_first_one"
        new_dict['new_password2'] = "this_is_totally_random_second_one_and_different"
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}), new_dict)
        self.assertContains(response, error_didnt_match)
        self.assertContains(response, error_either_didnt_match_or)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # three elements: wrong old, new_pw1, new_pw2 (equal) => error =>
    #                                       => "Your old password was entered incorrectly. Please enter it again."
    def test_ch_pw_three_wrong_old_pw_1_pw2_equal(self):
        new_dict = default_dict.copy()
        new_dict['old_password'] = test_password+"this_is_wrong_now"
        new_dict['new_password1'] = random_pw
        new_dict['new_password2'] = random_pw
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}), new_dict)
        self.assertContains(response, error_incorrect_old)
        self.assertNotContains(response, error_didnt_match)
        self.assertNotContains(response, error_either_didnt_match_or)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # three elements: correct old, new_pw1, new_pw2 (equal) => Success => and change password
    def test_ch_pw_three_correct_old_pw_1_pw2_equal(self):
        new_dict = default_dict.copy()
        new_dict['old_password'] = test_password
        new_dict['new_password1'] = random_pw
        new_dict['new_password2'] = random_pw
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    new_dict, follow=True)
        # check used template
        self.assertTemplateUsed(response, user_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=random_pw)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # three elements: correct old, new_pw1, new_pw2 (similar to username) => error =>
    #               => "Either the two password fields didn&#39;t match or additional restrictions are not fullfilled."
    #               => "The password is too similar to the username."
    def test_ch_pw_three_to_similar_to_username_correct(self):
        new_dict = default_dict.copy()
        new_dict['old_password'] = test_password
        new_dict['new_password1'] = user_name*2
        new_dict['new_password2'] = user_name*2
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    new_dict, follow=True)
        self.assertContains(response, error_too_similar_to+"the username.")
        self.assertContains(response, error_either_didnt_match_or)
        self.assertNotContains(response, error_didnt_match)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # three elements: correct old, new_pw1, new_pw2 (similar to email) => error =>
    #               => "Either the two password fields didn&#39;t match or additional restrictions are not fullfilled."
    #               => "The password is too similar to the email address."
    def test_ch_pw_three_to_similar_to_email_correct(self):
        new_dict = default_dict.copy()
        new_dict['old_password'] = test_password
        new_dict['new_password1'] = test_email
        new_dict['new_password2'] = test_email
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    new_dict, follow=True)
        self.assertContains(response, error_either_didnt_match_or)
        self.assertContains(response, error_too_similar_to+"the email address.")
        self.assertNotContains(response, error_didnt_match)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    """
    # three elements: correct old, new_pw1, new_pw2 (similar to first name) => error =>
    #               => "Either the two password fields didn&#39;t match or additional restrictions are not fullfilled."
    #               => "The password is too similar to the first name."
    def test_ch_pw_three_to_similar_to_first_name_correct(self):
        new_dict = default_dict.copy()
        new_dict['old_password'] = test_password
        new_dict['new_password1'] = first_name
        new_dict['new_password2'] = first_name
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    new_dict, follow=True)
        self.assertContains(response, error_too_similar_to+"the first name.")
        self.assertContains(response, error_either_didnt_match_or)
        self.assertNotContains(response, error_didnt_match)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")

    # three elements: correct old, new_pw1, new_pw2 (similar to last name) => error =>
    #               => "Either the two password fields didn&#39;t match or additional restrictions are not fullfilled."
    #               => "The password is too similar to the last name."
    def test_ch_pw_three_to_similar_to_last_name_correct(self):
        new_dict = default_dict.copy()
        new_dict['old_password'] = test_password
        new_dict['new_password1'] = last_name
        new_dict['new_password2'] = last_name
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    new_dict, follow=True)
        self.assertContains(response, error_too_similar_to+"the last name.")
        self.assertContains(response, error_either_didnt_match_or)
        self.assertNotContains(response, error_didnt_match)
        # check used template
        self.assertTemplateUsed(response, edit_template)
        self.client.logout()
        # verify the old password ist still correct and it has not been set to an empty pw
        # NOTE: therefore we need to verify the credentials and use login instead of force_login
        success = self.client.login(username=user_name, password=test_password)
        self.assertTrue(success, "FATAL: password has been changed, maybe it is empty now")
    """

    def test_ch_email_correct(self):
        new_email = "new@email.com"
        new_dict = default_dict.copy()
        new_dict['email'] = new_email
        new_dict['old_password'] = test_password
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    new_dict, follow=True)
        self.assertTemplateUsed(response, user_template)
        current_user = get_user_model().objects.get(username=user_name)
        self.assertEqual(current_user.email, new_email)

    def test_ch_email_empty_pw(self):
        new_email = "new@email.com"
        new_dict = default_dict.copy()
        new_dict['email'] = new_email
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    new_dict, follow=True)
        self.assertTemplateUsed(response, edit_template)
        current_user = get_user_model().objects.get(username=user_name)
        self.assertEqual(current_user.email, test_email)

    def test_ch_email_wrong_pw(self):
        new_email = "new@email.com"
        new_dict = default_dict.copy()
        new_dict['email'] = new_email
        new_dict['old_password'] = "wrong password"
        response = self.client.post(reverse('user_profile:edit_profile', kwargs={"username": user_name}),
                                    new_dict, follow=True)
        self.assertTemplateUsed(response, edit_template)
        current_user = get_user_model().objects.get(username=user_name)
        self.assertEqual(current_user.email, test_email)
