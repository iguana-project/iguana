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

t_LPAREN = r'\('
t_RPAREN = r'\)'


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
    raise Exception(u"Please note that the usage of control characters is not possible until escaping is implemented." +
                    u" Also the error might be caused by a neighbouring character." +
                    u" - Not able to parse char: '{}' in '{}'".format(t.value[0], t.value))
