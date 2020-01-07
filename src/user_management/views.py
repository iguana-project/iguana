"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.views.generic import View
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView as D_LIV, LogoutView as D_LOV, \
                                      PasswordResetView as D_PRV, PasswordResetDoneView as D_PRDV
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.encoding import force_bytes, force_text
from django.utils.http import is_safe_url, urlsafe_base64_encode, urlsafe_base64_decode
from django.urls import reverse


from django.conf import settings

from .forms import RegistrationForm
from .generate_activation_token import account_activation_token

# NOTE: ugettext_lazy "is essential when calls to these functions are located in code
#       paths that are executed at module load time."
from django.utils.translation import ugettext as _, ugettext_lazy as _l
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache


# TODO FormView might help to simplify this class
class LoginView(D_LIV):
    hide_breadcrumbs = True
    template_name = "registration/login.html"

    def get_success_url(self):
        url = self.get_redirect_url()
        return url or reverse("landing_page:home")


class LogoutView(D_LOV):
    hide_breadcrumbs = True
    template_name = "registration/login.html"

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        logged_out = 0
        if request.user.is_active:
            # the user gets logged out in the super() call later
            logged_out = 1
        self.extra_context = {'form': AuthenticationForm(), 'logged_out': logged_out}
        return D_LOV.dispatch(self, request, *args, **kwargs)


# https://docs.djangoproject.com/en/1.10/topics/forms/
# https://docs.djangoproject.com/en/1.10/topics/class-based-views/generic-display/
# TODO FormView might help to simplify this class
# this view creates an account which is not activated until the confirmation link send via email has been requested
# NOTE: This view can be used to leak usernames and email addresses that are already in use.
#       Those leaks are limited to requests where the captcha has been solved successfully.
class SignUpView(View):
    form_class = RegistrationForm
    # "When specifying a custom form class, you must still specify the model,
    #  even though the form_class may be a ModelForm."
    # https://docs.djangoproject.com/en/1.10/topics/class-based-views/generic-editing/
    model = get_user_model()
    hide_breadcrumbs = True

    def post(self, request):
        form = self.form_class(request.POST)

        """
        # NOTE: this is only enabled with js and it copies the previous provided data
        if 'submit_refresh_captcha' in request.POST:
            print("REFRESH")
            copy = request.POST.copy()
            delete_elements = ['captcha_0', 'captcha_1', 'csrfmiddlewaretoken']
            for el in delete_elements:
                try:
                    copy[el] = ""
                except:
                    pass
            form = self.form_class(copy)
            return render(request, 'registration/sign_up.html', {'form': form})
        """

        if form.is_valid():
            # the user is not active until the activation url has been requested
            new_user = form.save(commit=False)
            new_user.is_active = False
            # create the user that can be authenticated later on
            new_user.save()
            # TODO in case the email address is not verified within the next seven days the user shall be removed

            # content of the email that includes the activation url
            email = EmailMessage(
                # subject
                _('Verify your email address for ' + settings.PLATFORM),
                # body
                render_to_string('registration/activate_account_email_template.htm', {
                    'user': new_user,
                    'platform': settings.PLATFORM,
                    # url-elements
                    'domain': get_current_site(request).domain,
                    'uid': urlsafe_base64_encode(force_bytes(new_user.pk)),
                    'token': account_activation_token.make_token(new_user),
                }),
                # TODO as soon as there is a parameter in the settings to provide the from field it shall be used here
                # to
                to=[form.cleaned_data.get('email')],
            )
            email.send()

            return render(request, 'registration/email_confirmation.html')

        # remove errors for email and username if captcha failed so it is only possible
        # to leak registered usernames and email addresses if the captcha was provided correctly
        # otherwise this would result in a more harmful privacy leak
        if form.errors and 'captcha' in form.errors:
            non_critical_user_err_msg = _("@ is not allowed in username. Username is required as 150 characters or " +
                                          "fewer. Letters, digits and ./+/-/_ only.")
            if "username" in form.errors and non_critical_user_err_msg not in form.errors['username']:
                del form.errors['username']
            if "email" in form.errors:
                del form.errors['email']

        return render(request, 'registration/sign_up.html', {'form': form})

    def get(self, request):
        return render(request, 'registration/sign_up.html', {'form': self.form_class()})


# this view verifies the activation url
# s.a. https://simpleisbetterthancomplex.com/tutorial/2016/08/24/how-to-create-one-time-link.html
class VerifyEmailAddress(View):
    model = get_user_model()
    hide_breadcrumbs = True

    def get(self, request, *args, **kwargs):
        uidb64 = kwargs['uidb64']
        token = kwargs['token']
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = self.model.objects.get(id=uid)
        except(TypeError, ValueError, OverflowError, self.model.DoesNotExist):
            user = None
        if user is not None and account_activation_token.check_token(user, token):
            messages.info(request, _("Thanks for registering. You are now logged in."))
            user.is_active = True
            user.save()
            login(request, user)
            return HttpResponseRedirect(reverse("landing_page:home"))
        else:
            return render(request, 'registration/invalid_activation_link.html')


# TODO reactivate as soon as the bug is fixed
# TODO BUG does it work as intended again?
# TODO BUG sends wrong url for local (development) settings example.com != localhost:port
class PasswordResetView(D_PRV):
    breadcrumb = _l("Reset password")
    template_name = "registration/password_reset_form.html"


# TODO BUG does it work as intended again?
class PasswordResetSuccessView(D_PRDV):
    breadcrumb = _l("")
    template_name = "registration/password_reset_done.html"
