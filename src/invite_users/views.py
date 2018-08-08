"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.views.generic import FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.shortcuts import render

from .forms import InviteUserForm, EmailFormSet, EmailFormField
from django.forms import formset_factory
from django.conf import settings

# NOTE: ugettext_lazy "is essential when calls to these functions are located in code
#       paths that are executed at module load time."
from django.utils.translation import ugettext as _, ugettext_lazy as _l


# TODO redesign of this page
# TODO correct integration of this functionality into iguana
# TODO use some functionality of the FormView instead of this code written by my own
class InviteUserView(LoginRequiredMixin, FormView):
    form_class = InviteUserForm
    default_message = _l("Hello, you have been invited to ")+settings.PLATFORM + str(_l(" by"))
    max_number_of_invitables = 15
    breadcrumb = _l("Invite")

    def get(self, request):
        formset = formset_factory(EmailFormField, extra=0, max_num=self.max_number_of_invitables,
                                  min_num=1, validate_max=True, formset=EmailFormSet)
        cp = request.GET.copy()
        # TODO how can i provide the platform via function to the template?
        #      somehow i couldn't call the desired function from template
        return render(request, 'invite_users/invite_users.html', {'form': self.form_class(), 'formset': formset,
                                                                  'platform': settings.PLATFORM})

    def post(self, request):
        form = self.form_class(request.POST)
        MyEmailFormSet = formset_factory(EmailFormField, extra=0,
                                         max_num=self.max_number_of_invitables,
                                         min_num=1, validate_max=True, formset=EmailFormSet)

        # user wants to invite more people ('invite_more' is the name-tag of the submit button)
        # thanks to http://brantsteen.com/blog/django-adding-inline-formset-rows-without-javascript/
        # for this non-js solution
        if 'invite_more' in request.POST:
            # we copy the previous elements
            cp = request.POST.copy()
            number_of_people = int(cp['form-TOTAL_FORMS'])

            number_of_people += 1
            cp['form-TOTAL_FORMS'] = number_of_people
            additional_email = MyEmailFormSet(cp)
            return render(request, 'invite_users/invite_users.html', {'form': form, 'formset': additional_email,
                                                                      'platform': settings.PLATFORM})

        formset = MyEmailFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            inviting_user = request.user.get_username()
            additional_message = request.POST['additional_message']
            full_message = self.default_message+inviting_user+".\n\n"+additional_message
            invited_list = []

            to_header = []
            for f in formset:
                cleaned_data = f.cleaned_data
                target_email = cleaned_data.get('email')
                if target_email is not None:
                    invited_list.append(target_email)
                    if settings.EMAIL_RECIPIENT_IN_TO_HEADER:
                        to_header.append(target_email)

            # this is better than send_mail because bcc is possible
            email = EmailMessage(
                # subject
                _('You have been invited to ')+settings.PLATFORM,
                full_message,
                # TODO as soon as there is a parameter in the settings to provide the from field it shall be used here
                # to
                to=to_header,
                # bcc
                bcc=invited_list,
            )
            email.send()

            # list all notified email addresses in succesfully_invited
            request.session['invite_list'] = invited_list
            return HttpResponseRedirect('successfully_invited')

        return render(request, 'invite_users/invite_users.html', {'form': form, 'formset': formset,
                                                                  'platform': settings.PLATFORM})


class SuccessView(LoginRequiredMixin, View):
    breadcrumb = _l("")

    def get(self, request):
        try:
            invite_list = request.session['invite_list']
            request.session.pop('invite_list', None)
            request.session.modified = True
        except:
            invite_list = []
        return render(request, 'invite_users/successfully_invited.html', {'invite_list': invite_list})
