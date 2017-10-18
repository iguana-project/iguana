"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.test import TestCase
from django.core import mail

subject = 'Testmail subject'
body = 'Testmail message body'


class SendmailTest(TestCase):
    def test_sendmail(self):
        mail.send_mail(
            subject, body,
            'from@example.com', ['to@example.com'],
            fail_silently=False,
        )

        # check outbox
        self.assertEqual(len(mail.outbox), 1)

        # verify subject and body
        self.assertEqual(mail.outbox[0].subject, subject)
        self.assertEqual(mail.outbox[0].body, body)
