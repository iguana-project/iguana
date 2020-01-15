"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django import template
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.template import Node, TemplateSyntaxError
from django.http import QueryDict
from django.utils.encoding import smart_str
import re
import datetime
register = template.Library()

day_si = _("Day")
day_pl = _("Days")
hour_si = _("Hour")
hour_pl = _("Hours")
minute_si = _("Minute")
minute_pl = _("Minutes")
und = _(" and ")


@register.filter(name='issue_title')
def issue_title_short(td):
    if len(td) < 30:
        return td
    else:
        return td[:27]+"..."


@register.filter(name='duration')
def duration(td):
    total_seconds = int(td.total_seconds())
    ret = ''
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    def pluralize(x, s):
        if x > 1:
            if s == 0:
                return str(day_pl)
            elif s == 1:
                return str(hour_pl)
            else:
                return str(minute_pl)

        elif s == 0:
            return str(day_si)
        elif s == 1:
            return str(hour_si)
        else:
            return str(minute_si)

    if days > 0 and hours > 0 and minutes > 0:
        ret += str(days) + " "
        ret += pluralize(days, 0)
        ret += ', '
        ret += str(hours) + " "
        ret += pluralize(hours, 1)
        ret += str(und)
        ret += str(minutes) + " "
        ret += pluralize(minutes, 2)
    elif days > 0 and hours > 0:
        ret += str(days) + " "
        ret += pluralize(days, 0)
        ret += str(und)
        ret += str(hours) + " "
        ret += pluralize(hours, 1)
    elif days > 0 and minutes > 0:
        ret += str(days) + " "
        ret += pluralize(days, 0)
        ret += str(und)
        ret += str(minutes) + " "
        ret += pluralize(minutes, 2)
    elif hours > 0 and minutes > 0:
        ret += str(hours) + " "
        ret += pluralize(hours, 1)
        ret += str(und)
        ret += str(minutes) + " "
        ret += pluralize(minutes, 2)
    else:
        if days > 0:
            ret += str(days) + " "
            ret += pluralize(days, 0)

        if hours > 0:
            ret += str(hours) + " "
            ret += pluralize(hours, 1)

        if minutes > 0:
            ret += str(minutes) + " "
            ret += pluralize(minutes, 2)
    return ret


@register.filter(name='diff')
def diff(dtime):
    diff = timezone.now()-dtime
    if diff.total_seconds() < 60:
        diff = datetime.timedelta(seconds=60)
    return duration(diff)


@register.tag
def query_string(parser, token):
    """
    Template tag for creating and modifying query strings.

    Syntax:
        {% query_string  [<base_querystring>] [modifier]* [as <var_name>] %}

        modifier is <name><op><value> where op in {=, +, -}

    Parameters:
        - base_querystring: literal query string, e.g. '?tag=python&tag=django&year=2011',
                            or context variable bound to either
                            - a literal query string,
                            - a python dict with potentially lists as values, or
                            - a django QueryDict object
                            May be '' or None or missing altogether.
        - modifiers may be repeated and have the form <name><op><value>.
                           They are processed in the order they appear.
                           name is taken as is for a parameter name.
                           op is one of {=, +, -}.
                           = replace all existing values of name with value(s)
                           + add value(s) to existing values for name
                           - remove value(s) from existing values if present
                           value is either a literal parameter value
                             or a context variable. If it is a context variable
                             it may also be bound to a list.
        - as <var name>: bind result to context variable instead of injecting in output
                         (same as in url tag).

    Examples:
    1.  {% query_string  '?tag=a&m=1&m=3&tag=b' tag+'c' m=2 tag-'b' as myqs %}

        Result: myqs == '?m=2&tag=a&tag=c'

    2.  context = {'qs':   {'tag': ['a', 'b'], 'year': 2011, 'month': 2},
                   'tags': ['c', 'd'],
                   'm': 4,}

        {% query_string qs tag+tags month=m %}

        Result: '?tag=a&tag=b&tag=c&tag=d&year=2011&month=4
    """
    # matches 'tagname1+val1' or 'tagname1=val1' but not 'anyoldvalue'
    mod_re = re.compile(r"^(\w+)(=|\+|-)(.*)$")
    bits = token.split_contents()
    qdict = None
    mods = []
    asvar = None
    bits = bits[1:]
    if len(bits) >= 2 and bits[-2] == 'as':
        asvar = bits[-1]
        bits = bits[:-2]
    if len(bits) >= 1:
        first = bits[0]
        if not mod_re.match(first):
            qdict = parser.compile_filter(first)
            bits = bits[1:]
    for bit in bits:
        match = mod_re.match(bit)
        if not match:
            raise TemplateSyntaxError("Malformed arguments to query_string tag")
        name, op, value = match.groups()
        mods.append((name, op, parser.compile_filter(value)))
    return QueryStringNode(qdict, mods, asvar)


class QueryStringNode(Node):
    def __init__(self, qdict, mods, asvar):
        self.qdict = qdict
        self.mods = mods
        self.asvar = asvar

    def render(self, context):
        mods = [(smart_str(k, 'ascii'), op, v.resolve(context))
                for k, op, v in self.mods]
        if self.qdict:
            qdict = self.qdict.resolve(context)
        else:
            qdict = None
        # Internally work only with QueryDict
        qdict = self._get_initial_query_dict(qdict)
        # assert isinstance(qdict, QueryDict)
        for k, op, v in mods:
            qdict.setlist(k, self._process_list(qdict.getlist(k), op, v))
        qstring = qdict.urlencode()
        if qstring:
            qstring = '?' + qstring
        if self.asvar:
            context[self.asvar] = qstring
            return ''
        else:
            return qstring

    def _get_initial_query_dict(self, qdict):
        if not qdict:
            qdict = QueryDict(None, mutable=True)
        elif isinstance(qdict, QueryDict):
            qdict = qdict.copy()
        elif isinstance(qdict, (str, bytes)):
            if qdict.startswith('?'):
                qdict = qdict[1:]
            qdict = QueryDict(qdict, mutable=True)
        else:
            # Accept any old dict or list of pairs.
            try:
                pairs = qdict.items()
            except Exception:
                pairs = qdict
            qdict = QueryDict(None, mutable=True)
            # Enter each pair into QueryDict object:
            try:
                for k, v in pairs:
                    # Convert values to unicode so that detecting
                    # membership works for numbers.
                    if isinstance(v, (list, tuple)):
                        for e in v:
                            qdict.appendlist(k, str(e))
                    else:
                        qdict.appendlist(k, str(v))
            except Exception:
                # Wrong data structure, qdict remains empty.
                pass
        return qdict

    def _process_list(self, current_list, op, val):
        if not val:
            if op == '=':
                return []
            else:
                return current_list
        # Deal with lists only.
        if not isinstance(val, (list, tuple)):
            val = [val]
        val = [str(v) for v in val]
        # Remove
        if op == '-':
            for v in val:
                while v in current_list:
                    current_list.remove(v)
        # Replace
        elif op == '=':
            current_list = val
        # Add
        elif op == '+':
            for v in val:
                current_list.append(v)
        return current_list
