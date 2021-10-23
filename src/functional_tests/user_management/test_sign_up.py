"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from lib.selenium_test_case import SeleniumTestCase
from selenium.webdriver.common.by import By
from django.core import mail
from django.urls import reverse
import re
import sqlite3

from django.conf import settings


"""
Testing DB:
load database
  sqlite3 <database>
formatting output
  .header on
  .mode column
check table names
  .tables
select statement
  SELECT * FROM <table_name>;

NOTE: django uses a separated database for testing, which is not the production database.
"""

# this needs to be the same as defined in common/settings/development.py - NAME
DATABASE_PATH = settings.DATABASES['default']['NAME']
# this needs to be the same as defined in common/settings/development.py - TEST - NAME
TEST_DATABASE_PATH = settings.DATABASES['default']['TEST']['NAME']

test_username = "testuserName"
test_email = "test@thrash.com"
test_pw = "randomPa$_$word123"


class SignUpTest(SeleniumTestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_reachable_and_elements_exist(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('sign_up')))
        self.assertNotIn('Not Found', self.selenium.page_source)
        self.assertIn('Sign Up', self.selenium.title)

        register_form = self.selenium.find_element(By.ID, 'id_register_form')
        register_form.find_element(By.ID, 'id_username')
        register_form.find_element(By.ID, 'id_email')
        register_form.find_element(By.ID, 'id_password1')
        register_form.find_element(By.ID, 'id_password2')
        register_form.find_element(By.ID, 'id_submit_sign_up')

    # helper function to create a user
    def create_user(self, user_provided, email_provided, password_provided, password_provided_2):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('sign_up')))

        register_form = self.selenium.find_element(By.ID, 'id_register_form')
        user = register_form.find_element(By.ID, 'id_username')
        user.send_keys(user_provided)
        # register_form.find_element(By.ID, 'id_username').send_keys(user_provided)
        email = register_form.find_element(By.ID, 'id_email')
        email.send_keys(email_provided)
        password = register_form.find_element(By.ID, 'id_password1').send_keys(password_provided)
        password2 = register_form.find_element(By.ID, 'id_password2').send_keys(password_provided_2)
        captcha = register_form.find_element(By.ID, 'id_captcha_1').send_keys("PASSED")
        register_form.find_element(By.ID, 'id_submit_sign_up').click()

    def test_create_user(self):
        # create connection to database
        conn = sqlite3.connect(TEST_DATABASE_PATH)

        database = conn.cursor()
        user_table = "user_management_customuser"

        # create a new user
        self.create_user(test_username, test_email, test_pw, test_pw)

        # TODO fix replacement of example.com as soon as the dev-settings are fixed
        temp_activation_link = re.findall("https://.*/activate/.*/.*", mail.outbox[0].body)[0][len("https://"):]
        local_activation_link = temp_activation_link.replace("example.com", "")
        self.selenium.get("{}{}".format(self.live_server_url, local_activation_link))

        self.assertNotIn('Sign Up', self.selenium.title)
        self.assertEqual('Dashboard', self.selenium.title)

        # verify whether the new user has been created
        # conn = sqlite3.connect(DATABASE_PATH)
        # database = conn.cursor()
        user_already_exists = database.execute("SELECT * FROM "+user_table+" WHERE username=? OR email=?",
                                               (test_username, test_email, ))
        self.assertTrue(user_already_exists.fetchone() is not None)
        conn.close()

    def test_dont_duplicate_user(self):
        # create connection to database
        conn = sqlite3.connect(TEST_DATABASE_PATH)

        database = conn.cursor()
        user_table = "user_management_customuser"

        # create a new user
        self.create_user(test_username, test_email, test_pw, test_pw)
        # TODO fix replacement of example.com as soon as the dev-settings are fixed
        temp_activation_link = re.findall("https://.*/activate/.*/.*", mail.outbox[0].body)[0][len("https://"):]
        local_activation_link = temp_activation_link.replace("example.com", "")
        self.selenium.get("{}{}".format(self.live_server_url, local_activation_link))

        self.selenium.get("{}{}".format(self.live_server_url, reverse('logout')))
        self.assertIn("You have been successfully logged out.", self.selenium.page_source)

        # duplicated username + email
        self.create_user(test_username, test_email, test_pw, test_pw)
        self.assertIn('User with this Email address already exists.', self.selenium.page_source)
        self.assertIn('A user with that username already exists.', self.selenium.page_source)
        user_already_exists = database.execute("SELECT * FROM "+user_table+" WHERE username=? OR email=?",
                                               (test_username, test_email, ))
        self.assertEqual(len(user_already_exists.fetchall()), 1)

        # change email, so only the username is already in use
        test_email2 = "test@thrash.com2"
        self.create_user(test_username, test_email2, test_pw, test_pw)
        self.assertIn('A user with that username already exists.', self.selenium.page_source)
        user_doesnt_exists = database.execute("SELECT * FROM "+user_table+" WHERE username=? AND email=?",
                                              (test_username, test_email2, ))
        self.assertTrue(user_doesnt_exists.fetchone() is None)

        # change username, so only the email address is already in use
        test_username2 = "testuserName2"
        self.create_user(test_username2, test_email, test_pw, test_pw)
        self.assertIn('User with this Email address already exists.', self.selenium.page_source)
        user_doesnt_exists = database.execute("SELECT * FROM "+user_table+" WHERE username=? AND email=?",
                                              (test_username2, test_email, ))
        self.assertTrue(user_doesnt_exists.fetchone() is None)

        conn.close()

    def test_password_didnt_match(self):
        test_pw_2 = "randomPassword124"
        user_table = "user_management_customuser"

        # create a new user
        self.create_user(test_username, test_email, test_pw, test_pw_2)
        self.assertIn("The two password fields didn't match.", self.selenium.page_source)

    def test_dissallow_at_in_username(self):
        test_username = "testuser@Name"

        # create a new user
        self.create_user(test_username, test_email, test_pw, test_pw)
        self.assertIn("@ is not allowed in username. Username is required as 150 characters or " +
                      "fewer. Letters, digits and ./+/-/_ only.", self.selenium.page_source)
        self.assertNotIn('Dashboard', self.selenium.title)

    def test_dissallow_at_in_username_help_text(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('sign_up')))
        helptext = self.selenium.find_element(By.CSS_SELECTOR, '.help-block').text
        self.assertIn("Required. 150 characters or fewer. Letters, digits and ./+/-/_ only.", helptext)
        # maybe the wrong (original) help text is shown
        self.assertNotIn("@", helptext)

    # test buttons
    def test_goto_login(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('sign_up')))
        self.selenium.find_element(By.ID, 'id_login_ref').click()
        self.assertIn('Login', self.selenium.title)

    def test_goto_password_forgotten(self):
        self.selenium.get("{}{}".format(self.live_server_url, reverse('sign_up')))
        self.selenium.find_element(By.ID, 'id_reset_ref').click()
        self.assertIn('Password Reset', self.selenium.title)

    # TODO TESTCASE check delivered password guidelines
