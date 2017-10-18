"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import ply.lex as lex
from datetime import date

tokens = (
    'LPAREN',
    'RPAREN',
    'COMPARATOR',
    'FIELD',
    'STRING',
    'DATE',
    'NUMBER',
    'BOOL_OPERATOR',
    'SORT_OPERATOR',
    'SORTORDER_OPERATOR',
    'LIMIT',
)

# ignore spaces and tabs
t_ignore = ' \t'

# define all boolean operators
bool_ops = ('AND', 'OR')

# define all operators
sort_ops = ('SORT')
sortorder_ops = ('DESC', 'ASC')
limit_ops = ('LIMIT')

# comparison:
#   ==, !=: EQ, NEQ
#   <, >, <=, >=: LT, GT, LE, GE
#   ~: contains
#   ~~: regex
t_COMPARATOR = r'[!=]=|[<>]=?|~~?'

t_LPAREN = '\('
t_RPAREN = '\)'


# the name of the field to query:
#   starts with a letter and contains [a-zA-Z0-9_.] more than once
def t_FIELD(t):
    r'[a-zA-Z][\w\.]+'
    if t.value in bool_ops:
        t.type = 'BOOL_OPERATOR'
        return t
    if t.value in sortorder_ops:
        t.type = 'SORTORDER_OPERATOR'
        return t
    if t.value in sort_ops:
        t.type = 'SORT_OPERATOR'
        return t
    if t.value in limit_ops:
        t.type = 'LIMIT'
        return t

    t.value = t.value.replace('.', '__')
    return t


# string: everything between quotation marks and exclude quotation marks in sequence
# strip surrounding quotation marks before returning
def t_STRING(t):
    r'"[^"]*"'
    t.value = t.value[1:-1]
    return t


# date: everything following the convention yyyyddmm (only digits)
def t_DATE(t):
    r'(?P<year>\d{4})(?P<month>\d{2})(?P<day>\d{2})'
    day = int(t.lexer.lexmatch.group('day'))
    month = int(t.lexer.lexmatch.group('month'))
    year = int(t.lexer.lexmatch.group('year'))
    t.value = date(year, month, day)
    return t


# number: all other numeric values
def t_NUMBER(t):
    r'\d+'
    t.value = int(t.value)
    return t


# error handling
def t_error(t):
    raise Exception(u"Not able to parse char: %s" % t.value[0])
