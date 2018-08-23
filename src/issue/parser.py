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
import re

from issue.lexer import tokens
import issue.lexer

from django.db.models import Q

from .models import Issue
from tag.models import Tag
from kanbancol.models import KanbanColumn
from timelog.models import Timelog
from timelog.forms import DurationField
from user_management.models import CustomUser
from event import signals

# NOTE: This has been deactivated by default. If False it is possible to add a new dev without overwriting
#       the previous ones and the necessity to rewrite them all in the expression.
#       If you want to reactivate the previous behaviour simply set the value in the configuration to True.
from common.settings import OLEA_REPLACE_DEVS

# global attributes
attrs_to_set = []
issue_to_change = None
glob_project = None
glob_user = None
issue_created = False
issue_changed = False
duration_field = DurationField
cleanup_asignee = OLEA_REPLACE_DEVS
timelogs = []


# compose issue and change expression
def p_finalxpr(p):
    '''xpr : refissue cchgxpr
           | newissue cchgxpr
           | newissue'''

    p[0] = p[1]


# define an issue expression referencing an already existing issue
def p_refissue(p):
    '''refissue : ISSUE'''

    # set global var to existing issue
    global issue_to_change
    p[1] = resolve_issuedescription(p[1])
    splitname = p[1].split('-')
    issue_to_change = Issue.objects.filter(project__name_short=splitname[0],
                                           number=splitname[1]).first()

    # check existance and write permissions
    if issue_to_change is None or not issue_to_change.project.developer_allowed(glob_user):
        raise Exception(u'No valid issue reference given')
    p[0] = p[1]


# define a text expression for new issue creation
def p_newissue(p):
    '''newissue : TITLE'''

    # order delayed creation of new issue with given title
    # creation is delayed to avoid creation in case of errors in change expressions
    global issue_to_change
    global issue_created
    issue_created = True
    issue_to_change = p[1]
    p[0] = p[1]


# define a compounded change expression
def p_chgxpr(p):
    '''cchgxpr : chgxpr
               | cchgxpr chgxpr'''

    p[0] = p[1]


# define a change expression
def p_tagxpr(p):
    '''chgxpr : TAG'''

    # put xpr to attrs list
    global attrs_to_set
    global issue_changed

    project = glob_project
    if type(issue_to_change) is Issue:
        # we have an already existing issue, use it's project for tag search
        project = issue_to_change.project

    resultset = Tag.objects.filter(project=project,
                                   tag_text__icontains=p[1])
    if len(resultset) != 1:
        if len(resultset.filter(tag_text=p[1])) != 1:
            raise Exception(u"Given tag does not uniquely exist")
        resultset = resultset.filter(tag_text=p[1])

    attrs_to_set.append(['tags', resultset.first()])
    issue_changed = True
    p[0] = p[1]


def p_descrxpr(p):
    '''chgxpr : DESCR'''

    # put xpr to attrs list
    global attrs_to_set
    global issue_changed

    attrs_to_set.append(['description', p[1]])
    issue_changed = True
    p[0] = p[1]


def p_statusxpr(p):
    '''chgxpr : STATUS'''

    project = glob_project
    if type(issue_to_change) is Issue:
        # we have an already existing issue, use it's project for tag search
        project = issue_to_change.project

    resultset = KanbanColumn.objects.filter(project=project,
                                            name__icontains=p[1])

    if len(resultset) != 1:
        if len(resultset.filter(name=p[1])) != 1:
            raise Exception(u"Given kanban column does not uniquely exist")
        resultset = resultset.filter(name=p[1])

    attrs_to_set.append(['kanbancol', resultset.first()])
    issue_changed = True
    p[0] = p[1]


# define a change expression
def p_userxpr(p):
    '''chgxpr : USER'''

    # put xpr to attrs list
    global attrs_to_set
    global issue_changed

    project = glob_project
    if type(issue_to_change) is Issue:
        # we have an already existing issue, use it's project for user search
        project = issue_to_change.project

    # set of users that are either developer or manager for current project
    # and either their username or first or last name matches given username
    resultset = CustomUser.objects.filter((Q(dev_projects=project) |
                                           Q(manager=project)) &
                                          (Q(username__icontains=p[1]) |
                                           Q(first_name__icontains=p[1]) |
                                           Q(last_name__icontains=p[1]))
                                          ).distinct()
    # contains comparison is problematic if we have a username that is
    # part of another username, this would result in a queryset size of 2,
    # so we have to check if the username of the first element is equal to p[1]
    if len(resultset) != 1:
        if len(resultset.filter(username=p[1])) != 1:
            raise Exception(u"Given user does not uniquely exist")
        resultset = resultset.filter(username=p[1])

    attrs_to_set.append(['assignee', resultset.first()])
    issue_changed = True
    p[0] = p[1]


# define a change expression
def p_prioxpr(p):
    '''chgxpr : PRIO'''

    # put xpr to attrs list
    global attrs_to_set
    global issue_changed

    attrs_to_set.append(['priority', p[1]])
    issue_changed = True
    p[0] = p[1]


# define a change expression
def p_storyptsxpr(p):
    '''chgxpr : STORYPOINTS'''

    # put storypoints to attrs list
    global attrs_to_set
    global issue_changed

    attrs_to_set.append(['storypoints', p[1]])
    issue_changed = True
    p[0] = p[1]


# define a change expression
def p_typexpr(p):
    '''chgxpr : TYPE'''

    # put xpr to attrs list
    global attrs_to_set
    global issue_changed

    attrs_to_set.append(['type', p[1]])
    issue_changed = True
    p[0] = p[1]


# define a change expression
def p_dependsxpr(p):
    '''chgxpr : DEPENDS'''

    # put xpr to attrs list
    global attrs_to_set
    global issue_changed

    project = glob_project
    if type(issue_to_change) is Issue:
        # we have an already existing issue, use it's project for tag search
        project = issue_to_change.project

    p[1] = resolve_issuedescription(p[1])
    splitname = p[1].split('-')
    resultset = Issue.objects.filter(project__name_short=splitname[0],
                                     number=splitname[1],
                                     project=project)
    if len(resultset) != 1:
        raise Exception(u"Given depends issue does not uniquely exist")

    attrs_to_set.append(['dependsOn', resultset.first()])
    issue_changed = True
    p[0] = p[1]


# define a change expression
def p_timelogxpr(p):
    '''chgxpr : TIMELOG'''

    # skip if expression is empty
    if p[1] == '':
        return

    # convert string to timediff and store in timelog object
    tdiff = DurationField.to_python(self=duration_field, value=p[1])
    global timelogs
    timelogs.append(tdiff)
    p[0] = p[1]


# set error behavior
def p_error(p):
    raise Exception(u"Parsing error: unexpected end of expression")


# resolve an issue descriptor with optional project to a complete descriptor
def resolve_issuedescription(descr):
    pattern = re.compile("^[0-9]+")
    if pattern.match(descr):
        # we only have issue number: add project descriptor to retval
        return glob_project.name_short + "-" + descr
    else:
        # we have a complete project name
        return descr


def compile(expression, project, user):
    global attrs_to_set
    global issue_to_change
    global glob_project
    global glob_user
    global issue_created
    global cleanup
    global cleanup_asignee
    global timelogs
    global issue_changed
    issue_created = False
    issue_changed = False
    cleanup_asignee = OLEA_REPLACE_DEVS
    attrs_to_set = []
    timelogs = []
    issue_to_change = ""
    glob_project = project
    glob_user = user

    # check that user has write access to project
    if not project.developer_allowed(user):
        raise Exception(u"No user permissions to modify issues in this project")

    # parse expression
    lexer = lex.lex(module=issue.lexer)
    # writes to parsetab.py (this is closed internally) and parser.out (which seems to stay open)
    # I don't know why debuglog (parser.out) is still open if we provide our own PlyLogger with it's
    # own file descriptor in that case yacc should not open any files.
    parser = yacc.yacc()
    parser.parse(expression, lexer=lexer)
    # TODO BUG cleanup yacc - close and parser.out, Y TFH is there no destructor doing this for us?
    # NOTE ^this doesn't seem to be possible - s. comment above

    # create issue if necessary
    if issue_created:
        issue_to_change = Issue(title=issue_to_change,
                                project=glob_project,
                                kanbancol=glob_project.kanbancol.first(),
                                creator=glob_user)
        issue_to_change.save()

    if issue_changed:
        changed_data = signals.fields_to_changed_data(issue_to_change, [tup[0] for tup in attrs_to_set])

    # handle timelogging separately
    for tdiff in timelogs:
        timelog = Timelog(user=glob_user, issue=issue_to_change, time=tdiff)
        timelog.save()

    for attr in attrs_to_set:
        # process all parsed attributes to change
        field = issue_to_change.__getattribute__(attr[0])

        if str(type(field)).startswith("<class 'django.db.models"):
            # cleanup assignee before setting first new assignee
            if attr[0] == "assignee" and cleanup_asignee:
                cleanup_asignee = False
                field.clear()

            # we have a related field -> call add
            field.add(attr[1])
        else:
            # no db model field, simply assign value
            issue_to_change.__setattr__(attr[0], attr[1])
            issue_to_change.save()

    if issue_created:
        signals.create.send(sender=Issue, instance=issue_to_change, user=user)

    if not issue_created and issue_changed:
        signals.modify.send(sender=Issue, instance=issue_to_change, user=user, changed_data=changed_data)
