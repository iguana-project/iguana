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
