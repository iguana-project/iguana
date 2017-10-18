"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import ply.yacc as yacc
import ply.lex as lex
from django.db.models import Q

from search.lexer import tokens
import search.lexer
import search.frontend

comparatorToQExpression = {
    '==': '',
    '!=': '',
    '>': 'gt',
    '>=': 'gte',
    '<': 'lt',
    '<=': 'lte',
    '~': 'regex',
    '~~': 'contains',
}

obj_to_query = ''
sort_by = []
limit = -1


# allow limiting and sorting
def p_query_limit_sort(p):
    '''query : expression
            | query limit
            | query sortexpr'''
    p[0] = p[1]


# allow limiting
def p_limit(p):
    '''limit : LIMIT NUMBER'''
    global limit
    limit = p[2]


# define a sort expression
def p_result_sort(p):
    '''sortexpr : SORT_OPERATOR SORTORDER_OPERATOR target'''
    global sort_by
    sort = p[3]
    if p[2] == 'DESC':
        sort = '-' + sort

    sort_by.append(sort)


# allow parenthesized expressions
def p_expression_parentheses(p):
    '''expression : LPAREN expression RPAREN'''
    p[0] = p[2]


# define a value
def p_value(p):
    '''value : STRING
            | NUMBER
            | DATE'''
    p[0] = p[1]


# define a target
def p_target(p):
    '''target : FIELD'''

    # split field into obj and field
    split = p[1].split('__', 1)
    obj = split[0]
    field = split[1]

    global obj_to_query
    if obj_to_query == '':
        obj_to_query = obj

    # check field searchability
    if search.frontend.SearchFrontend.check_field_searchability(obj, field) is False:
        raise Exception(u"Search on invalid field")

    p[0] = field


# define an expression
def p_expression(p):
    '''expression : target COMPARATOR value'''

    comp = comparatorToQExpression[p[2]]

    field = p[1]

    if comp:
        field = '%s__%s' % (field, comp)

    field = str(field)
    d = {field: p[3]}
    p[0] = Q(**d)

    if p[2] == '!=':
        p[0] = ~ p[0]


# allow concatenating expressions with boolean operator
def p_expression_boolOp(p):
    '''expression : expression BOOL_OPERATOR expression'''
    if p[2] == 'AND':
        p[0] = p[1] & p[3]
    elif p[2] == 'OR':
        p[0] = p[1] | p[3]


# set error behavior
def p_error(p):
    raise Exception(u"Parsing error: unexpected end of expression")


def compile(expression):
    global obj_to_query
    global sort_by
    global limit
    obj_to_query = ''
    sort_by = []
    limit = -1
    lexer = lex.lex(module=search.lexer)
    parser = yacc.yacc()
    return parser.parse(expression, lexer=lexer)
