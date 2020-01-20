"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from pagedown.widgets import PagedownWidget
from bootstrap_datepicker_plus._base import BasePickerInput
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.functional import Promise
from django.utils.encoding import force_text
from json import dumps as json_dumps
from lib.user_language import get_user_locale_lazy, get_user_locale_format_lazy
from django.utils import formats
from bootstrap_datepicker_plus import DateTimePickerInput, DatePickerInput
from dal_select2.widgets import ModelSelect2Multiple, Select2WidgetMixin,\
    ModelSelect2
import re
from django.forms.widgets import Media


class CustomPagedownWidget(PagedownWidget):
    @property
    def media(self):
        # get the default js and css media
        media = super().media

        # add custom js
        new_js = media._js
        new_js.append("js/pagedown_iguana_markdown.js")

        # add custom css
        new_css = media._css
        new_css["all"].append("css/pagedown.css")

        return Media(js=tuple(new_js), css=new_css)


class LocalizedBasePickerInput(BasePickerInput):
    # This JSON encoder is needed for encoding lazy objects (mostly translated language strings)
    class LazyEncoder(DjangoJSONEncoder):
        def default(self, obj):
            if isinstance(obj, Promise):
                return force_text(obj)
            return DjangoJSONEncoder.default(self, obj)

    # the default format key how the value is displayed
    display_format_key = 'DATE_FORMAT'

    # don't show the current date and/or time when opening the picker the first time
    BasePickerInput.options["useCurrent"] = False

    def __init__(self, attrs=None, format=None, options={}):
        if settings.USE_I18N:
            options["locale"] = get_user_locale_lazy()
        if settings.USE_L10N:
            # ignore the 'format' option
            options.pop("format", None)
            format = None
            # lazyly load the right format
            self.format = get_user_locale_format_lazy(self.display_format_key)

        # reset options to default 'None' if no change was made above
        if not options:
            options = None
        BasePickerInput.__init__(self, attrs=attrs, format=format, options=options)

    def _calculate_format(self):
        if settings.USE_L10N:
            # the right format is loaded already in the constructor above
            return self.format
        else:
            return BasePickerInput._calculate_format(self)

    def get_context(self, name, value, attrs):
        """Return widget context dictionary."""
        context = super(BasePickerInput, self).get_context(name, value, attrs)
        context['widget']['attrs']['dp_config'] = json_dumps(self.config, cls=LocalizedBasePickerInput.LazyEncoder)
        return context

    def format_value(self, value):
        if self.format and \
                isinstance(self.format, Promise):
            return formats.localize_input(value, force_text(self.format))
        else:
            return super().format_value(value=value)

    @property
    def media(self):
        # get the default js and css media
        media = super().media

        # add custom js
        regex = re.compile(r"^https://cdnjs\.cloudflare\.com/.*$")
        filtered_js = [item for item in media._js if not regex.search(item)]
        filtered_js.append("js/bootstrap-datetimepicker/bootstrap-datetimepicker.min.js")
        filtered_js.append("js/bootstrap-datetimepicker/moment-with-locales.min.js")

        # add custom css
        filtered_css = [item for item in media._css["all"] if not regex.search(item)]
        filtered_css.append("css/bootstrap-datetimepicker.min.css")

        return Media(js=tuple(filtered_js), css={"all": filtered_css})


class LocalizedDateTimePickerInput(DateTimePickerInput, LocalizedBasePickerInput):
    display_format_key = 'SHORT_DATETIME_FORMAT'


class LocalizedDatePickerInput(DatePickerInput, LocalizedBasePickerInput):
    display_format_key = 'DATE_FORMAT'


class CustomSelect2WidgetMixin(Select2WidgetMixin):
    @property
    def media(self):
        # get the default js and css media
        media = super().media

        # remove the jQuery script manually
        # this causes errors with datepicker-plus,
        # see https://github.com/monim67/django-bootstrap-datepicker-plus/issues/42
        # TODO this code patch can be removed in future,
        # because of https://github.com/yourlabs/django-autocomplete-light/commit/e46300d
        regex = re.compile(r"^admin/.*jquery(\.min)?\.js$")
        filtered_js = [item for item in media._js if not regex.search(item)]

        # add custom css
        new_css = media._css
        new_css["screen"].append("css/autocomplete-light.css")

        return Media(js=tuple(filtered_js), css=new_css)


class CustomAutoCompleteWidgetSingle(ModelSelect2, CustomSelect2WidgetMixin):
    pass


class CustomAutoCompleteWidgetMultiple(ModelSelect2Multiple, CustomSelect2WidgetMixin):
    pass
