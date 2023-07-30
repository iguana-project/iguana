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
from lib.multiform import MultiFormsView
from django import forms
from django.http.response import HttpResponseRedirect
from django.contrib.auth.models import AbstractUser


fClassesNames = ('customForm', 'defaultForm')
groupName = 'group1'
initialDict = {'initial': 'initial'}
requestMethodNames = ('data', 'files')
form_valid = False


def custom_is_valid(*args, **kwargs):
    return form_valid


# this class defines a custom form that is required for testing
class CustomForm(forms.ModelForm):
    class Meta:
        model = AbstractUser
        fields = ('username',)


class TempMultiform(MultiFormsView):
    template_name = '_base.html'
    form_classes = {
            fClassesNames[0]: CustomForm,
            fClassesNames[1]: forms.Form
        }
    grouped_forms = {
            groupName: (fClassesNames[1],)
        }
    success_url = 'my/success/url'

    # add some additional required fields
    def request(self):
        return None
    setattr(request, 'method', 'POST')
    setattr(request, 'POST', requestMethodNames[0])
    setattr(request, 'FILES', requestMethodNames[1])
    object = AbstractUser

    def __init__(self):
        # call the request method once for fulfilling coverage
        self.request()

    def get_defaultForm_initial(self):
        return initialDict

    def create_defaultForm_form(self, **form_kwargs):
        if 'instance' in form_kwargs:
            return forms.Form(form_kwargs.pop('instance'))
        else:
            return forms.Form(**form_kwargs)

    def defaultForm_form_valid(self, forms, form):
        return super(TempMultiform, self).form_valid(forms, form)

    def form_valid(self, forms, form):
        return super(TempMultiform, self).form_valid(forms, form)

    def defaultForm_form_invalid(self, forms, form):
        return super(TempMultiform, self).form_invalid(forms, form)


class MultiformTest(TestCase):
    def setUp(self):
        # NOTE: these elements get modified by some testcases, so they should NOT be created in setUpTestData()
        self.tempForm = TempMultiform()
        # save the is_valid method of the form class
        self.formIsValidMethod = getattr(forms.Form, 'is_valid')
        # override is_valid method of the forms
        setattr(forms.Form, 'is_valid', custom_is_valid)
        setattr(CustomForm, 'is_valid', custom_is_valid)

    def tearDown(self):
        # restore the is_valid method
        setattr(forms.Form, 'is_valid', self.formIsValidMethod)

    def test_simple_methods(self):
        # test get_form_classes()
        classes = self.tempForm.get_form_classes()
        self.assertEqual(self.tempForm.form_classes, classes)

        # test get_forms()
        forms = self.tempForm.get_forms(self.tempForm.form_classes)
        for key in self.tempForm.form_classes:
            self.assertIsInstance(forms[key], self.tempForm.form_classes[key])

        # test get_form_kwargs() with bind_form=True
        kwargs = self.tempForm.get_form_kwargs(fClassesNames[1], True)
        self.assertEqual(kwargs['initial'], initialDict)

        # test form_valid()
        redirect = self.tempForm.form_valid(forms, None)
        self.assertEqual(redirect.url, self.tempForm.success_url)

        # test forms_invalid()
        response = self.tempForm.forms_invalid(forms, fClassesNames[1])
        self.assertEqual(response.status_code, 200)

        # test get_success_url()
        url = self.tempForm.get_success_url()
        self.assertEqual(url, self.tempForm.success_url)

    def test_formsBinding(self):
        # get request object
        requestObj = self.tempForm.__class__.__dict__['request']

        # first test method POST
        result = self.tempForm._bind_form_data()
        self.assertEqual(result['data'], requestMethodNames[0])
        self.assertEqual(result['files'], requestMethodNames[1])

        # then test another method
        setattr(requestObj, 'method', 'something else')
        result = self.tempForm._bind_form_data()
        self.assertEqual(result, {})

        # reset the POST method
        setattr(requestObj, 'method', 'POST')

    def test_createForm(self):
        # save the object value
        obj = getattr(self.tempForm, 'object')

        for key, value in self.tempForm.form_classes.items():
            form = self.tempForm._create_form(key, value, False)
            self.assertIsInstance(form, self.tempForm.form_classes[key])
            # delete the object attribute
            if hasattr(self.tempForm, 'object'):
                delattr(self.tempForm.__class__, 'object')

        # restore the saved object value
        setattr(self.tempForm.__class__, 'object', obj)

    def test_formsValid(self):
        forms = self.tempForm.get_forms(self.tempForm.form_classes)
        for key, _ in self.tempForm.form_classes.items():
            redirect = self.tempForm.forms_valid(forms, key)
            self.assertEqual(redirect.url, self.tempForm.success_url)

    def test_get(self):
        response = self.tempForm.get(None)
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        requestObj = self.tempForm.__class__.__dict__['request']
        actionParam = (fClassesNames[1], groupName, '')

        for i in range(0, 6):
            setattr(requestObj, 'POST', {'action': actionParam[i % 3]})

            response = self.tempForm.post(requestObj)
            if isinstance(response, HttpResponseRedirect):
                self.assertEqual(response.url, self.tempForm.success_url)
            else:
                self.assertEqual(response.status_code, 200)

            if i == 2:
                global form_valid
                form_valid = True

        setattr(requestObj, 'POST', requestMethodNames[0])

    def test_response_forbidden(self):
        form_classes = self.tempForm.get_form_classes()
        response = self.tempForm._process_individual_form('no form', form_classes)
        self.assertEqual(response.status_code, 403)
