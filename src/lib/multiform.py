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
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django.views.generic.edit import ProcessFormView
from django.http.response import HttpResponseRedirect, HttpResponseForbidden

"""
Usage example:

class SignupLoginView(MultiFormsView):
    template_name = 'public/my_login_signup_template.html'
    form_classes = {'login': LoginForm,
                    'signup': SignupForm}
    success_url = 'my/success/url'

    def get_login_initial(self):
        return {'email':'dave@dave.com'}

    def get_signup_initial(self):
        return {'email':'dave@dave.com'}

    def get_context_data(self, **kwargs):
        context = super(SignupLoginView, self).get_context_data(**kwargs)
        context.update({"some_context_value": 'blah blah blah',
                        "some_other_context_value": 'blah'})
        return context

    def login_form_valid(self, form):
        return form.login(self.request, redirect_url=self.get_success_url())

    def signup_form_valid(self, form):
        user = form.save(self.request)
        return form.signup(self.request, user, self.get_success_url())

    def create_login_form(self, **kwargs):
        return LoginForm(kwargs.pop('instance'), **kwargs)
"""


class MultiFormMixin(ContextMixin):
    """
    Mixin that allows multiple forms in a class based view.
    """

    form_classes = {}
    """
    Register all from classes in this directory.
    Example: form_classes = {
                'form_name1': form_class1,
                'form_name2': form_class2
            }
    """

    prefixes = {}
    """
    Register a prefix for a form.
    Example: prefixes = {
                'form_name1': 'prefix1',
                'form_name2': 'prefix2'
            }
    """

    success_urls = {}
    """
    Register a success URL for each form name.
    Example: success_urls = {
                'form_name1': 'url1',
                'form_name2': 'url2'
            }
    """

    grouped_forms = {}
    """
    Specify a group of form names.
    Example: grouped_forms = {
                'group_name1': ['form_name1', 'form_name2'],
                'group_name2': ['form_name3', 'form_name4']
            }
    """

    initial = {}
    """
    Register initials for this view.
    Example: initial = {'subject': 'Hi there!'}
    """

    prefix = None
    """
    Here you can specify a global prefix for all forms in this view.
    """

    success_url = ""
    """
    Here you can specify a global success URL for all forms in this view.
    """

    def get_form_classes(self):
        """
        Get the form classes.
        """
        return self.form_classes

    def get_forms(self, form_classes, form_names=None, bind_all=False):
        """
        Get a dictionary (form_name, form_class) with the forms that are specified by the parameter form_names.
        """
        return dict([(key, self._create_form(key, klass, (form_names and key in form_names) or bind_all))
                     for key, klass in form_classes.items()])

    def get_form_kwargs(self, form_name, bind_form=False):
        """
        Setup the kwargs for a form.
        """
        kwargs = {}
        kwargs.update({'initial': self.get_initial(form_name)})
        kwargs.update({'prefix': self.get_prefix(form_name)})

        if bind_form:
            kwargs.update(self._bind_form_data())

        return kwargs

    def form_valid(self, forms, form):
        """
        If the form is valid, redirect to the supplied URL.
        """
        return HttpResponseRedirect(self.get_success_url())

    def form_invalid(self, forms, form):
        """
        If the form is invalid, redirect to the response.
        """
        return self.render_to_response(self.get_context_data(forms=forms))

    def forms_valid(self, forms, form_name, isGroup=False):
        """
        This method is called if a form is validated.
        It runs the form_valid method of the view either global for all forms or for each form individual.
        """
        # the default method name of the form valid method
        default_valid_method = 'form_valid'
        # the individual name for each form
        form_valid_method = '{}_form_valid'.format(form_name)

        # for a group, multiple forms get passed
        if isGroup:
            form = [forms[form] for form in self.grouped_forms[form_name]]
        else:
            form = forms[form_name]

        if hasattr(self, form_valid_method):
            # first check for the individual method
            return getattr(self, form_valid_method)(forms, form)
        else:  # the default method must be in the class, because it's defined here
            # then call the default method
            return getattr(self, default_valid_method)(forms, form)

    def forms_invalid(self, forms, form_name, isGroup=False):
        """
        This method is called if a form of this view can't be validated.
        """
        # the default method name of the form invalid method
        default_invalid_method = 'form_invalid'
        # the individual name for each form
        form_invalid_method = '{}_form_invalid'.format(form_name)

        # for a group, multiple forms get passed
        if isGroup:
            form = [forms[form] for form in self.grouped_forms[form_name]]
        else:
            form = forms[form_name]

        if hasattr(self, form_invalid_method):
            # first check for the individual method
            return getattr(self, form_invalid_method)(forms, form)
        else:  # the default method must be in the class, because it's defined here
            # then call the default method
            return getattr(self, default_invalid_method)(forms, form)

    def get_initial(self, form_name):
        """
        For each form a initial method can be declared.
        It is run when the form is created.

        The method MUST return a dictionary with the initial values.
        """
        initial_method = 'get_{}_initial'.format(form_name)
        if hasattr(self, initial_method):
            # run the specific initial method
            return getattr(self, initial_method)()
        else:
            # return the default initial dictionary
            return self.initial.copy()

    def get_prefix(self, form_name):
        """
        Returns the prefix for a specific form.
        Or if not defined, the global prefix.
        """
        return self.prefixes.get(form_name, self.prefix)

    def get_success_url(self, form_name=None):
        """
        Returns the success URL for a specific form.
        Or if not defined, the global success URL.
        """
        return self.success_urls.get(form_name, self.success_url)

    def _create_form(self, form_name, klass, bind_form):
        """
        This method creates a from.
        """
        # get the kwargs for a form
        form_kwargs = self.get_form_kwargs(form_name, bind_form)

        # check if a this view contains a 'object' attribute
        if hasattr(self, 'object'):
            # if so, add it to the kwargs as 'instance' (needed by some views)
            form_kwargs.update({'instance': self.object})

        # get the create method for a form
        form_create_method = 'create_{}_form'.format(form_name)
        if hasattr(self, form_create_method):
            # call the create method
            form = getattr(self, form_create_method)(**form_kwargs)
        else:
            # instantiate the class as usual
            form = klass(**form_kwargs)
        return form

    def _bind_form_data(self):
        """
        Bind data to the form.
        """
        if self.request.method in ('POST', 'PUT'):
            return{'data': self.request.POST,
                   'files': self.request.FILES, }
        return {}


class ProcessMultipleFormsView(ProcessFormView):
    """
    This class handles the POST and GET requests for the forms.
    """
    def get(self, request, *args, **kwargs):
        """
        The GET request renders the specified forms.
        When overriding this method please call super()
        """
        # render the forms of the view
        form_classes = self.get_form_classes()
        forms = self.get_forms(form_classes)
        return self.render_to_response(self.get_context_data(*args, **kwargs, forms=forms))

    def post(self, request, *args, **kwargs):
        """
        The POST request calls the handles the form(s) and checks if it's valid.
        When overriding this method please call super()
        """
        form_classes = self.get_form_classes()
        # get the form name by the 'action' attribute of the corresponding button
        form_name = request.POST.get('action')
        if self._individual_exists(form_name):
            # the button had a specific form as 'action' attribute -> process the single form
            return self._process_individual_form(form_name, form_classes)
        elif self._group_exists(form_name):
            # the button belongs to a group of forms -> process the group
            return self._process_grouped_forms(form_name, form_classes)
        else:
            # the button has no 'action' attribute -> process all forms of this view
            return self._process_all_forms(form_classes)

    def _individual_exists(self, form_name):
        """
        This method checks if a specific form name is registered in the form_classes dictionary.
        """
        return form_name in self.form_classes

    def _group_exists(self, group_name):
        """
        This method checks if a specific group name is registered in the grouped_forms dictionary.
        """
        return group_name in self.grouped_forms

    def _process_individual_form(self, form_name, form_classes):
        """
        Perform the is_valid() check for a single form.
        """
        forms = self.get_forms(form_classes, (form_name,))
        form = forms.get(form_name)
        if not form:
            # there is no form with this name registered in the form_classes dictionary
            return HttpResponseForbidden()
        elif form.is_valid():
            # the form is valid -> call the from valid method
            return self.forms_valid(forms, form_name)
        else:
            # call the form invalid method
            return self.forms_invalid(forms, form_name)

    def _process_grouped_forms(self, group_name, form_classes):
        """
        Perform the is_valid() check for a group of forms.
        """
        form_names = self.grouped_forms[group_name]
        forms = self.get_forms(form_classes, form_names)
        # check if all forms are valid
        if all([forms[formName].is_valid() for formName in forms if formName in form_names]):
            # process the group valid method
            self.forms_valid(forms, group_name, isGroup=True)

            # redirect to success url if at least one form was valid
            return HttpResponseRedirect(self.get_success_url())
        else:
            # process the group invalid method
            self.forms_invalid(forms, group_name, isGroup=True)

            # show errors instead
            return self.render_to_response(self.get_context_data(forms=forms))

    def _process_all_forms(self, form_classes):
        """
        Perform the is_valid() check for all forms.
        """
        forms = self.get_forms(form_classes, None, True)
        # only proceed if all forms are valid
        if all([form.is_valid() for form in forms.values()]):
            for form_name in forms:
                # for every form call the valid method
                self.forms_valid(forms, form_name)

            # redirect to the success URL
            return HttpResponseRedirect(self.get_success_url())
        else:
            for form_name in [form for form in forms if not forms[form].is_valid()]:
                # for every invalid form call the invalid method
                self.forms_invalid(forms, form_name)

            # show errors instead
            return self.render_to_response(self.get_context_data(forms=forms))


class BaseMultipleFormsView(MultiFormMixin, ProcessMultipleFormsView):
    """
    A base view for displaying several forms.
    """


class MultiFormsView(TemplateResponseMixin, BaseMultipleFormsView):
    """
    A view for displaying several forms, and rendering a template response.
    """
