# contains several helper functions that should be used in the testcases to simplify them
# TODO use this everywhere!

from django.urls import reverse
from user_management.views import LoginView
from rest_framework import viewsets


# \param view the view that should be used
# \param template the template that should be used
# \param address_pattern the pattern for the reverse lookup that is used to resolve the target address
# \param address_kwargs optional additional kwargs arguments that might be needed for the resolving of the address
# \param get_kwargs optional additional kwargs for a get request that might be needed to specify
#        which content is desired
def view_and_template(self, view, template, address_pattern, address_kwargs=None, get_kwargs=None):
    if get_kwargs:
        response = self.client.get(reverse(address_pattern, kwargs=address_kwargs),  get_kwargs, follow=True)
    else:
        response = self.client.get(reverse(address_pattern, kwargs=address_kwargs), follow=True)
    if template:
        self.assertTemplateUsed(response, template)

    # catch the APIViewsTest for ProjectViewSet that need additional address_kwargs
    if issubclass(view, viewsets.ModelViewSet):
        self.assertEqual(response.resolver_match.func.__name__, view.as_view(address_kwargs).__name__)
    else:
        self.assertEqual(response.resolver_match.func.__name__, view.as_view().__name__)
    return response


# Checks for redirection to login page and a certain error message
# \param resolved_address The address after address resolution
# \param response The response from the client after address resolution
# \param expected_message The error message to be expected
def redirect_to_login_with_expected_message(self, resolved_address, response, expected_message):
    self.assertEqual(response.status_code, 302)
    self.assertEqual(response['location'], '/login/?next=' + resolved_address)
    response = self.client.get(response['location'])
    # verify the login-required mixin
    self.assertEqual(response.resolver_match.func.__name__, LoginView.as_view().__name__)
    self.assertContains(response, expected_message)


# LoginRequiredMixin
# uses get
# \param address_pattern The pattern for the reverse lookup that is used to resolve the target address
# \param address_kwargs Optional additional kwargs arguments that might be needed for the resolving of the address
# \param get_kwargs Optional additional kwargs for a get request that might be needed
#        to specify which content is desired
# \param alternate_error_message Optional error message that is shown instead of the default error message
def redirect_to_login_and_login_required(self, address_pattern, address_kwargs=None, get_kwargs=None,
                                         alternate_error_message=None):
    resolved_address = reverse(address_pattern, kwargs=address_kwargs)
    if get_kwargs:
        response = self.client.get(resolved_address, get_kwargs)
    else:
        response = self.client.get(resolved_address)

    expected_message = 'Please login to see this page.'
    if alternate_error_message:
        expected_message = alternate_error_message
    redirect_to_login_with_expected_message(self, resolved_address, response, expected_message)


# UserPassesTestMixin / test_func()
# uses post
# \param address_pattern The pattern for the reverse lookup that is used to resolve the target address
# \param address_kwargs Optional additional kwargs arguments that might be needed for the resolving of the address
# \param get_kwargs Optional additional kwargs for a get request that might be needed
#        to specify which content is desired
# \param alternate_error_message Optional error message that is shown instead of the default error message
def redirect_to_login_and_user_doesnt_pass_test(self, address_pattern, address_kwargs=None, get_kwargs=None,
                                                alternate_error_message=None):
    resolved_address = reverse(address_pattern, kwargs=address_kwargs)
    # uses post instead of get
    if get_kwargs:
        response = self.client.post(resolved_address, get_kwargs)
    else:
        response = self.client.post(resolved_address)

    expected_message = 'Your account doesn\'t have access to this page.'
    if alternate_error_message:
        expected_message = alternate_error_message
    redirect_to_login_with_expected_message(self, resolved_address, response, expected_message)


# TODO add further functions
