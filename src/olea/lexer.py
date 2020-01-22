"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import ply.lex as lex

tokens = (
    'ISSUE',
    'TITLE',
    'USER',
    'TAG',
    'DESCR',
    'STATUS',
    'PRIO',
    'TYPE',
    'DEPENDS',
    'TIMELOG',
    'STORYPOINTS',
)

types = ('Bug', 'Story', 'Task')

# ignore tabs
t_ignore = '\t'

# all tokens must be separated by a single space


# set asignee
#   starts with a @ followed by the asignee's name
#   strip @ before returning
def t_USER(t):
    r'[ ]{1}@[a-zA-Z0-9_\-\+\.]+'
    t.value = t.value[2:]
    return t


# set tag
#   starts with a # followed by the tag name and may not end with a space
#   strip # before returning
def t_TAG(t):
    r'[ ]{1}\#[a-zA-Z0-9_\-\+\. ]+[a-zA-Z0-9_\-\+\.]{1}'
    t.value = t.value[2:]
    return t


# set description
#   starts with a ; followed by the tag name and may not end with a space
#   strip ; before returning
def t_DESCR(t):
    r'[ ]{1};[\w\-\.\?\",/\(\) ]+[\w\-\.\?\",/\(\)]'
    t.value = t.value[2:]
    return t


# set status (kanbancolumn)
#   starts with a & followed by the tag name and may not end with a space
#   strip & before returning
def t_STATUS(t):
    r'[ ]{1}&[a-zA-Z0-9_\-\+\. ]+[a-zA-Z0-9_\-\+\.]{1}'
    t.value = t.value[2:]
    return t


# set prio
#   starts with a ! followed by a digit
def t_PRIO(t):
    r'[ ]{1}![0-4]{1}'
    t.value = t.value[2:]
    return t


# set storypoints
#   starts with a $ followed by a digit
def t_STORYPOINTS(t):
    r'[ ]{1}\$[0-9]+'
    t.value = t.value[2:]
    return t


# set type
#   starts with a : followed by the type
def t_TYPE(t):
    r'[ ]{1}:[BST]{1}[a-z]{2,4}'
    t.value = t.value[2:]
    if t.value not in types:
        raise Exception(u"Invalid issue type given")
    return t


# set dependent issue
#   starts with a ~ followed by the issue's name:
#   (1 to 4 letters and a number concatenated by a -)
def t_DEPENDS(t):
    r'[ ]{1}~([a-zA-Z]{1,4}-)?[0-9]+'
    t.value = t.value[2:]
    return t


# set time to log to issue
#   time consists of the optional parts hms with preceding decimal
def t_TIMELOG(t):
    r'[ ]\+(\d+d)?(\d+h)?(\d+m)?'
    t.value = t.value[2:]
    return t


# set issue to modify
#   starts with a > followed by an issue's name
#   first part of query line, so it must not start with whitespace
def t_ISSUE(t):
    r'>([a-zA-Z]{1,4}-)?[0-9]+'
    t.value = t.value[1:]
    return t


# title for new issue creation
#   plain text containing spaces, but starting with letter or number
#   must not end with a whitespace character
def t_TITLE(t):
    r'[\w][\w\-\.\?\",/\(\) ]+[\w\-\.\?\",/\(\)]'
    return t


# error handling
def t_error(t):
    raise Exception(u"Please note that the usage of control characters is not possible until escaping is implemented." +
                    u" Also the error might be caused by a neighbouring character." +
                    u" - Not able to parse char: '{}' in '{}'".format(t.value[0], t.value))
