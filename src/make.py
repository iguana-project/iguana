"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import argparse
import importlib
from importlib import util as import_util
import inspect
from io import StringIO
import json
import os
import platform
import shutil
import site
import subprocess
import sys
import tarfile
import textwrap
from urllib.request import urlopen
import venv
from subprocess import Popen, STDOUT


###########
# VARIABLES
###########
# base directories
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
FILES_DIR = os.path.join(BASE_DIR, "files")
STATIC_FILES = os.path.join(BASE_DIR, "static_files")

# settings file for the Makefile
MAKE_SETTINGS_FILE = os.path.join(BASE_DIR, ".makeSettings")

# virtualenv settings
VIRTUALENV_BASE_DIR = os.path.join(BASE_DIR, "virtualenv")
# add virtualenv bin directory to the PATH (because some executables need to be in PATH)
os.environ["PATH"] += ":" + os.path.join(VIRTUALENV_BASE_DIR, "bin")

# tools directory
TOOLS = os.path.join(BASE_DIR, "tools")

# Iguana settings
IGUANA_BASE_DIR = os.path.join(BASE_DIR, "src")
IGUANA_SCSS_DIR = os.path.join(IGUANA_BASE_DIR, "common", "scss")
IGUANA_SETTINGS_FILE = os.path.join(FILES_DIR, "settings.json")
WEBDRIVER_CONF_FILE = os.path.join(IGUANA_BASE_DIR, "common", "settings", "webdriver.py")

# django settings
DJANGO_SETTINGS_MODULE = "common.settings"
DJANGO_SETTINGS_FILE = os.path.join(IGUANA_BASE_DIR, "common", "settings", "__init__.py")

# coverage settings
COVERAGE_SETTINGS_FILE = os.path.join(IGUANA_BASE_DIR, ".coveragerc")
COVERAGE_DATA_FILE = os.path.join(IGUANA_BASE_DIR, ".coverage")

# git hooks directory
GITHOOK_DIR = os.path.join(BASE_DIR, ".git", "hooks")
# custom git hook directory
CUSTOM_GIT_HOOK_DIR = os.path.join(TOOLS, "git-hooks")

# log files directory
LOG_DIR = os.path.join(FILES_DIR, "logs")


############################
# TARGET/ARGUMENT DECORATORS
############################

def _add_variable_decorator(cls_to_decorate, name="", value=None, add_to_list=False):
    if add_to_list:
        if not isinstance(value, list):
            value = [value]

        # add the value to a list
        value_list = getattr(cls_to_decorate, name, [])
        setattr(cls_to_decorate, name, value_list + value)
    else:
        setattr(cls_to_decorate, name, value)

    return cls_to_decorate


def cmd(cmd=""):
    def wrap(cls):
        return _add_variable_decorator(cls, "cmd", cmd)
    return wrap


def arg(argument="", arg_short=None, arg_long=None):
    def wrap(cls):
        cls = _add_variable_decorator(cls, "arg", argument)
        cls.arg_short = arg_short
        cls.arg_long = arg_long
        return cls
    return wrap


def default(default=""):
    def wrap(cls):
        return _add_variable_decorator(cls, "default", default)
    return wrap


def required(cls):
    return _add_variable_decorator(cls, "is_required", True)


def boolean(cls):
    return _add_variable_decorator(cls, "is_boolean", True)


def multiple(cls):
    return _add_variable_decorator(cls, "is_multiple", True)


def group(group=""):
    def wrap(cls):
        return _add_variable_decorator(cls, "group", group)
    return wrap


def help(help=""):  # noqa
    def wrap(cls):
        return _add_variable_decorator(cls, "help", help)
    return wrap


def call_before(target=None):
    def wrap(cls):
        return _add_variable_decorator(cls, "call_before", target, add_to_list=True)
    return wrap


def call_after(target=None):
    def wrap(cls):
        return _add_variable_decorator(cls, "call_after", target, add_to_list=True)
    return wrap


################
# PARENT-CLASSES
################

class _MetaTarget(type):
    @property
    def child_targets(self):
        return [inner_cls for inner_cls in self.__dict__.values()
                if inspect.isclass(inner_cls) and issubclass(inner_cls, _Target)]

    @property
    def argument_values(self):
        cmd = self.super_parent_target.cmd
        if cmd not in self._argument_values:
            # the argument values are captured in a dictionary of their absolute parent target
            self._argument_values[cmd] = {}

        return self._argument_values

    @property
    def is_help_needed(self):
        # if contains child targets or arguments
        if self.child_targets or self.argument_classes:
            return True
        else:
            return False

    @property
    def super_parent_target(self):
        parent = self.parent_target
        # recursively get the absolute parent
        while parent and parent.parent_target:
            parent = parent.parent_target

        # return self class if it's already the parent
        if parent:
            return parent
        else:
            return self

    @property
    def parent_target(self):
        try:
            parent_name = self.__qualname__.split('.')[-2]
            parent_module = sys.modules[self.__module__]
            return vars(parent_module)[parent_name]
        except Exception:
            # there is no parent
            return None

    @property
    def has_parent(self):
        if self.parent_target is not None and \
                isinstance(self.parent_target, _Target):
            return True
        else:
            return False

    @property
    def argument_classes(self):
        return [inner_cls for inner_cls in self.__dict__.values()
                if inspect.isclass(inner_cls) and issubclass(inner_cls, _Argument)]


class _Target(argparse.Action, metaclass=_MetaTarget):
    # default values (Do not change these in subclasses! Instead use the decorators above!)
    cmd = ""
    group = ""
    help = ""
    call_before = []
    call_after = []
    _argument_values = {}

    @classmethod
    def execute_target(cls, parser, argument_values, argv_rest):
        # override this method!
        # by default it shows the help message
        _HelpTarget.execute_target(parser, argument_values, argv_rest)

    @classmethod
    def _get_callable_targets(cls, target_list=[]):
        for target in target_list:
            if issubclass(target, _Target):
                yield target

    @classmethod
    def _call_targets(cls, parser, argument_values, argv_rest):
        # call dependency targets
        for target in cls._get_callable_targets(cls.call_before):
            target._call_targets(parser, argument_values, argv_rest)

        # call the target
        cls.execute_target(parser, argument_values, argv_rest or "")

        # call dependent targets
        for target in cls._get_callable_targets(cls.call_after):
            target._call_targets(parser, argument_values, argv_rest)

    def __call__(self, parser, _, argv_rest, *unused):
        # do not execute the target if it has child targets and one of them is used
        choice_made_and_possible = False
        for action in parser._actions:
            if action.choices is not None:
                for choice in action.choices:
                    if str(choice) == sys.argv[-1]:
                        choice_made_and_possible = True
        if choice_made_and_possible:
            return

        # call the target with its dependecies
        self._call_targets(parser, type(self).argument_values[type(self).super_parent_target.cmd], argv_rest)


class _MetaArgument(type):
    @property
    def arg_short(self):
        return self._arg_short

    @arg_short.setter
    def arg_short(self, value):
        if value is None:
            value = self.arg[0]

        self._arg_short = '-' + str.lower(value)

    @property
    def arg_long(self):
        return self._arg_long

    @arg_long.setter
    def arg_long(self, value):
        if value is None:
            value = self.arg

        self._arg_long = "--" + str.lower(value)

    @property
    def parent_target(self):
        parent_name = self.__qualname__.split('.')[0:-1]
        parent_module = sys.modules[self.__module__]
        env = vars(parent_module)
        for path in parent_name:
            if path in env:
                cls = env[path]
                env = vars(cls)
            else:
                break
        return cls

    @property
    def parent_target_value(self):
        return self.parent_target.argument_values[self.parent_target.super_parent_target.cmd][self.arg]

    @parent_target_value.setter
    def parent_target_value(self, value):
        self.parent_target.argument_values[self.parent_target.super_parent_target.cmd][self.arg] = value


class _Argument(argparse.Action, metaclass=_MetaArgument):
    arg = ""
    _arg_short = ""
    _arg_long = ""
    default = None
    is_required = False
    is_boolean = False
    is_multiple = False
    help = ""

    def __init__(self,
                 option_strings,
                 dest,
                 nargs=None,
                 const=None,
                 default=None,
                 type=None,  # noqa
                 choices=None,
                 required=False,
                 help=None,  # noqa
                 metavar=None):
        # set values for _StoreConstAction
        if self.is_boolean:
            if default is None:
                default = False
            nargs = 0
            const = True

        # call the parent constructor
        argparse.Action.__init__(self, option_strings, dest, nargs=nargs, const=const, default=default, type=type,
                                 choices=choices, required=required, help=help, metavar=metavar)

        # set default value in the parent
        self.__class__.parent_target_value = default

    # on call add argument values to parent
    def __call__(self, parser, namespace, values, option_string):
        if self.is_boolean:
            # call _StoreConstAction action
            argparse._StoreTrueAction.__call__(self, parser, namespace, values, option_string)
            values = True

        # if multiple arguments are allowed, add them to a list
        if self.is_multiple:
            current_values = self.__class__.parent_target_value or []
            values = current_values + [values]

        # add the value to the target
        self.__class__.parent_target_value = values


# custom class to enable pseudo groups with subparsers (see https://bugs.python.org/issue9341)
class _SubParsersCustom(argparse._SubParsersAction):
    class _SubParsersGroup(argparse.Action):
        def __init__(self, container, title):
            argparse.Action.__init__(self, option_strings=[], dest=title)
            self.container = container
            self._choices_actions = []

        def add_parser(self, name, **kwargs):
            # add the parser to the main Action, but move the pseudo action
            # in the group's own list
            parser = self.container.add_parser(name, **kwargs)
            choice_action = self.container._choices_actions.pop()
            self._choices_actions.append(choice_action)
            return parser

        def _get_subactions(self):
            return self._choices_actions

        def add_parser_group(self, title):
            # the formatter can handle reursive subgroups
            grp = type(self)(self, title)
            self._choices_actions.append(grp)
            return grp

    def add_parser_group(self, title):
        grp = self._SubParsersGroup(self, title)
        self._choices_actions.append(grp)
        return grp

    # add action parameter to the method
    # if this parameter is specified, it is enough to call this subparser to execute the underlining action
    def add_parser(self, name, action=None, **kwargs):
        parser = argparse._SubParsersAction.add_parser(self, name, **kwargs)
        if action is not None and \
                issubclass(action, argparse.Action):
            parser.add_argument("none", action=action, nargs='?', help=argparse.SUPPRESS)
        return parser


#########
# TARGETS
#########

# class with operations used by multiple targets
class _MetaCommonTargets(type):
    @property
    def is_development(self):
        settings = self._get_dev_stage_setting()
        return settings["development"]

    @property
    def is_staging(self):
        settings = self._get_dev_stage_setting()
        return settings["staging"]


class _CommonTargets(metaclass=_MetaCommonTargets):
    @classmethod
    def remove_dev_stage_setting(cls):
        # remove the settings file if it exeists
        if os.path.isfile(MAKE_SETTINGS_FILE):
            os.remove(MAKE_SETTINGS_FILE)

    @classmethod
    def remove_virtualenv_directory(cls):
        if os.path.isdir(VIRTUALENV_BASE_DIR):
            shutil.rmtree(VIRTUALENV_BASE_DIR, ignore_errors=True)

    @classmethod
    def activate_virtual_environment(cls):
        # check if already a virtual environment is present
        # or running on Travis CI
        if sys.base_prefix != sys.prefix or \
                os.environ.get('TRAVIS') == 'true':
            return

        # check if a virtual environment can be activated
        virt_python = os.path.join(VIRTUALENV_BASE_DIR, "bin", "python")
        if not os.path.isfile(virt_python):
            cls.exit("No virtual environment is present! Please run 'setup-virtualenv'.", 1)

        # use the environment now
        script_file = __file__
        if script_file.endswith('.pyc'):
            script_file = script_file[:-1]
        try:
            result = subprocess.run([virt_python, script_file] + sys.argv[1:]).returncode
        except KeyboardInterrupt:
            # return no error when the process is interrupted by ctrl-c
            raise SystemExit(0)
        # all other cases
        raise SystemExit(result)

    @classmethod
    def get_requirements_file(cls):
        # check which requirements should be installed
        settings = cls._get_dev_stage_setting()
        requirements_file = os.path.join(BASE_DIR, "requirements")
        if settings["development"]:
            requirements_file = os.path.join(requirements_file, "development.req")
        elif settings["staging"]:
            requirements_file = os.path.join(requirements_file, "staging.req")
        else:
            requirements_file = os.path.join(requirements_file, "production.req")

        return requirements_file

    @classmethod
    def check_webdriver(cls):
        global WEBDRIVER
        if os.path.isfile(WEBDRIVER_CONF_FILE):
            import common.settings.webdriver as driver
            WEBDRIVER = driver.WEBDRIVER
        else:
            print("Default webdriver 'chrome' is used.")

    @classmethod
    def initialize_settings(cls):
        settings = cls._get_dev_stage_setting()

        # load side side_module
        spec = import_util.spec_from_file_location('manage_settings',
                                                   os.path.join(IGUANA_BASE_DIR, "lib", "manage_settings.py"))
        side_module = import_util.module_from_spec(spec)
        spec.loader.exec_module(side_module)

        # initialize settings
        side_module.initialize_secret_key(DJANGO_SETTINGS_FILE, IGUANA_SETTINGS_FILE, settings["development"])

    @classmethod
    def _get_dev_stage_setting(cls):
        if os.path.isfile(MAKE_SETTINGS_FILE):
            # open the settings file
            with open(MAKE_SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
        else:
            # default settings
            settings = {
                "development": False,
                "staging": False
            }

        return settings

    @classmethod
    def save_dev_stage_setting(cls, development=False, staging=False):
        # add the settings to a dictionary
        settings = {
            "development": development,
            "staging": staging
        }

        # open the settings file
        with open(MAKE_SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)

    @classmethod
    def link_git_hooks(cls):
        for hook in CUSTOM_GIT_HOOKS:
            # the path for the link destination
            hook_dest = os.path.join(GITHOOK_DIR, os.path.basename(hook))

            if os.path.islink(hook_dest) or \
                    os.path.isfile(hook_dest):
                os.remove(hook_dest)

            # the relative path to the source file
            hook_src = os.path.join(os.path.relpath(BASE_DIR, GITHOOK_DIR), hook)

            # create the system link
            os.symlink(hook_src, hook_dest)

    @classmethod
    def exec_django_cmd(cls, cmd, *args, **kwargs):
        cls.activate_virtual_environment()

        from django.core.management import call_command
        # this is needed for several Django actions
        from common import wsgi  # noqa

        # execute the command
        call_command(cmd, *args, **kwargs)

    @classmethod
    def exit(cls, error_msg=None, error_code=0):
        if error_code != 0 or error_msg is not None:
            print(error_msg, file=sys.stderr)

        sys.exit(error_code)


# override of argparse._HelpAction
@cmd("help")
@help("Show this help message and exit.")
class _HelpTarget(_Target):
    @property
    @classmethod
    def root_parser(cls):
            return cls._root_parser

    @root_parser.setter
    @classmethod
    def root_parser(cls, value):
            cls._root_parser = value

    @classmethod
    def execute_target(cls, parser, *unused):
        # print help if no choice is made at all
        if parser.prog.endswith(sys.argv[-1]) and sys.argv[-1] != "help":
            parser.print_help()
            parser.exit()
        # do nothing if it's not asked for help
        elif not parser.prog.endswith("help"):
            return

        # continue with the 'root' help
        root_parser = _HelpTarget.root_parser
        # print the help
        root_parser.print_help()

        # retrieve subparsers from parser
        subparsers_actions = [action for action in root_parser._actions
                              if isinstance(action, argparse._SubParsersAction)]

        # there will probably only be one subparser_action,
        # but better save than sorry
        for subparsers_action in subparsers_actions:
            # get all subparsers and print help
            for choice, subparser in subparsers_action.choices.items():
                # ignore the help target parser
                if subparser == parser:
                    continue

                print()
                print("==========")
                print(">   Target '{}'".format(choice))
                print(textwrap.indent(subparser.format_help(), '    '))

        root_parser.exit()


@cmd("run")
@group("Django management")
@help("Run the Django server locally.")
class _RunTarget(_Target):
    @classmethod
    def execute_target(cls, unused1, unused2, argv_rest):
        if _CommonTargets.is_development:
            # start the development server
            _CommonTargets.exec_django_cmd("runserver", argv_rest, settings=DJANGO_SETTINGS_MODULE)
        else:
            _CommonTargets.activate_virtual_environment()

            # start celery (worker and beat)
            Popen(["celery", "-A", "common", "worker", "-l", "info", "--pidfile="],
                  stderr=STDOUT, stdout=open(os.path.join(LOG_DIR, "celery-worker.log"), "w+"), bufsize=0,
                  cwd=IGUANA_BASE_DIR)
            Popen(["celery", "-A", "common", "beat", "-l", "info", "--pidfile="],
                  stderr=STDOUT, stdout=open(os.path.join(LOG_DIR, "celery-beat.log"), "w+"), bufsize=0,
                  cwd=IGUANA_BASE_DIR)

            # start gunicorn
            subprocess.run(["gunicorn", "-w", "8", "common.wsgi:application",
                            "--bind", "unix:" + os.path.join(BASE_DIR, "gunicorn.sock"),
                            "--access-logfile", os.path.join(LOG_DIR, "gunicorn-accesslog.log"),
                            "--error-logfile", os.path.join(LOG_DIR, "gunicorn-errorlog.log")], cwd=IGUANA_BASE_DIR)


@cmd("create-app")
@group("Django management")
@help("Create a new Django application.")
class _CreateAppTarget(_Target):
    @arg("APP_NAME")
    @required
    @help("The name of the new application.")
    class AppName(_Argument):
        pass

    @classmethod
    def execute_target(cls, unused1, argument_values, unused2):
        # create the new django application
        # a change to the Django directory is necessary because of a bug in the current 'startapp [destination]'
        #   implementation
        os.chdir(IGUANA_BASE_DIR)
        _CommonTargets.exec_django_cmd("startapp", argument_values["APP_NAME"], settings=DJANGO_SETTINGS_MODULE)
        os.chdir(BASE_DIR)


@cmd("migrations")
@group("Django management")
@help("Manage the Django migrations.")
class _MigrationsTarget(_Target):
    @cmd("create")
    @help("Create the Django migrations.")
    class Create(_Target):
        @classmethod
        def execute_target(cls, *unused):
            _CommonTargets.exec_django_cmd("makemigrations", settings=DJANGO_SETTINGS_MODULE)

    @cmd("apply")
    @help("Apply the Django migrations.")
    class Apply(_Target):
        @classmethod
        def execute_target(cls, *unused):
            _CommonTargets.exec_django_cmd("migrate", settings=DJANGO_SETTINGS_MODULE)


@cmd("test")
@group("Django management")
@help("Execute the Django tests.")
class _TestTarget(_Target):
    @arg("app")
    @multiple
    @help("The Django application name to test.")
    class AppName(_Argument):
        pass

    @arg("func-tests")
    @boolean
    @help("Execute the functional tests.")
    class FuncTests(_Argument):
        pass

    @arg("ign-imp-errs")
    @boolean
    @help("Run the Django tests without error-messages from imported packages.")
    class IgnImpErrs(_Argument):
        pass

    @arg("complete-test")
    @boolean
    @help("Run Django application AND functional tests.")
    class CompleteTest(_Argument):
        pass

    class IgnImpErrsOutWrapper(StringIO):
        def __init__(self, stdout):
            self.__stdout = stdout
            StringIO.__init__(self)

        def write(self, *args, **kwargs):
            # only write output, that does not contain 'virtualenv'
            write = False
            if isinstance(args, tuple):
                for arg in args:
                    if "virtualenv" not in arg:
                        write = True
            elif "virtualenv" not in args:
                write = True

            if write:
                self.__stdout.write(*args, **kwargs)
                StringIO.write(self, *args, **kwargs)

        def read(self, *args, **kwargs):
            self.seek(0)
            self.__stdout.write(StringIO.read(self, *args, **kwargs))

    @classmethod
    def execute_target(cls, unused1, argument_values, unused2):
        if _CommonTargets.is_development:
            nomigrations = True
        else:
            nomigrations = False

        # check if functional tests should be run
        if argument_values["func-tests"]:
            if argument_values["app"]:
                # execute only the functional tests of the specified app
                argument_values["app"] = ["functional_tests.%s" % app for app in argument_values["app"]]
            else:
                # execute all functional tests
                argument_values["app"] = ["functional_tests"]

        # override stdout and stderr
        if argument_values["ign-imp-errs"]:
            sys_stdout = sys.stdout
            sys_stderr = sys.stderr
            sys.stdout = _TestTarget.IgnImpErrsOutWrapper(sys.stdout)
            sys.stderr = _TestTarget.IgnImpErrsOutWrapper(sys.stderr)

        # ######### BLOCK START ##########
        # TODO workaround for failing testcases, if functional tests are executed right after the unit tests
        # the test cases have to be checked what exactly causes the problem
        # there are also errors if the unit tests get not executed in the default order
        # TODO remove this block after these errors are fixed
        if argument_values["complete-test"]:
            # execute the functional tests first
            _CommonTargets.exec_django_cmd("test", IGUANA_BASE_DIR, tags=["functional"], no_input=True,
                                           nomigrations=nomigrations, settings=DJANGO_SETTINGS_MODULE)

            # prevent the functional tests from getting executed again
            argument_values["complete-test"] = False
        # ######### BLOCK END ##########

        # execute the tests
        if argument_values["complete-test"]:
            # execute all tests (including the functional ones)
            _CommonTargets.exec_django_cmd("test", IGUANA_BASE_DIR, interactive=False, nomigrations=nomigrations,
                                           settings=DJANGO_SETTINGS_MODULE)
        else:
            if not argument_values["app"]:
                # execute all tests except the functional ones
                _CommonTargets.exec_django_cmd("test", IGUANA_BASE_DIR, exclude_tags=["functional"], interactive=False,
                                               nomigrations=nomigrations, settings=DJANGO_SETTINGS_MODULE)
            else:
                # execute only the specific application tests
                _CommonTargets.exec_django_cmd("test", *argument_values["app"], interactive=False,
                                               nomigrations=nomigrations, settings=DJANGO_SETTINGS_MODULE)

        # restore stdout and stderr
        if argument_values["ign-imp-errs"]:
            sys.stdout = sys_stdout
            sys.stderr = sys_stderr


@cmd("messages")
@group("Django management")
@help("Manage the Django messages.")
class _MessagesTarget(_Target):
    @cmd("create")
    @help("Create the Django messages.")
    class Create(_Target):
        @arg("lang-code")
        @default("en")
        @help("The language code for the messages.")
        class LangCode(_Argument):
            pass

        @classmethod
        def execute_target(cls, unused1, argument_values, unused2):
            _CommonTargets.exec_django_cmd("makemessages", "-l", argument_values["lang-code"],
                                           settings=DJANGO_SETTINGS_MODULE)

    @cmd("compile")
    @help("Compile the Django messages.")
    class Compile(_Target):
        @classmethod
        def execute_target(cls, *unused):
            _CommonTargets.exec_django_cmd("compilemessages", settings=DJANGO_SETTINGS_MODULE)


@cmd("collectstatic")
@group("Django management")
@help("Collect static files and copy them into /static_files.")
class _CollectionTarget(_Target):
    @classmethod
    def execute_target(cls, *unused):
        # collect the static files
        _CommonTargets.exec_django_cmd("collectstatic", "--noinput", settings=DJANGO_SETTINGS_MODULE)


@cmd("requirements")
@group("Source code management")
@help("Manage the requirements for this project.")
class _RequirementsTarget(_Target):
    @cmd("check")
    @help("Check if there are any updates of the requirements.")
    class Check(_Target):
        @classmethod
        def execute_target(cls, *unused):
            _CommonTargets.activate_virtual_environment()

            # import piprot
            from piprot import piprot
            # get the requirements file
            requirements_file = _CommonTargets.get_requirements_file()
            # execute piprot
            piprot.main([open(requirements_file, 'r')], verbose=True, outdated=True)

    @cmd("install")
    @help("(Re-)Install the requirements.")
    class Install(_Target):
        @classmethod
        def execute_target(cls, *unused):
            # check which requirements should be installed
            requirements_file = _CommonTargets.get_requirements_file()

            # install the requirements
            _CommonTargets.activate_virtual_environment()
            # fix for pip versions below 10.0
            try:
                from pip._internal import main as pipmain
            except ImportError:
                from pip import main as pipmain
            code = pipmain(["install", "-r", requirements_file])

            # check for possible errors
            if code != 0:
                _CommonTargets.exit("Failed while installing the requirements! Please check the errors above.", code)

            # reload the installed packages
            importlib.reload(site)


@cmd("setup-virtualenv")
@group("Source code management")
@call_after(_RequirementsTarget.Install)
@help("Create the virtual environment for Django.")
class _SetupVirtualenvTarget(_Target):
    @classmethod
    def execute_target(cls, *unused):
        # check if already a virtual environment is present
        virt_python = os.path.join(VIRTUALENV_BASE_DIR, "bin", "python")
        if not os.path.isfile(virt_python):
            # create a new environment
            venv.create(VIRTUALENV_BASE_DIR, with_pip=True)


@cmd("set-webdriver")
@group("Source code management")
@help("Set the browser that should be used for the functional tests.")
class _SetWebdriverTarget(_Target):
    @cmd("chrome")
    @help("Use Chrome browser for the webdriver.")
    class Chrome(_Target):
        @classmethod
        def execute_target(cls, *unused):
            cls.parent_target.use_browser(cls.cmd)

    @cmd("firefox")
    @help("Use Firefox browser for the webdriver.")
    class Firefox(_Target):
        @classmethod
        def execute_target(cls, *unused):
            cls.parent_target.use_browser(cls.cmd)

    @cmd("safari")
    @help("Use Safari browser for the webdriver.")
    class Safari(_Target):
        @classmethod
        def execute_target(cls, *unused):
            cls.parent_target.use_browser(cls.cmd)

    @classmethod
    def __install_chromedriver(cls):
        system = platform.system()
        if system == "Linux":
            # only 64bit driver is available for chromedriver
            system += "64"

        # the link destination
        dest_file = os.path.join(VIRTUALENV_BASE_DIR, "bin", "chromedriver")

        # the binary driver file (relative to the destination path above)
        driver_file = os.path.join(VIRTUALENV_BASE_DIR,
                                   "src", "chromedriver", "chromedriver", "bin", "chromedriver-" + system)
        driver_file = os.path.relpath(driver_file, os.path.dirname(dest_file))

        # link the driver binary
        if os.path.islink(dest_file) or \
                os.path.isfile(dest_file):
            os.remove(dest_file)
        os.symlink(driver_file, dest_file)

    @classmethod
    def __install_geckodriver(cls):
        response = urlopen("https://api.github.com/repos/mozilla/geckodriver/releases/latest")
        if response.code != 200:
            _CommonTargets.exit("No connection to the GitHub API is possible! Please try again later.", 1)
        # the API returns json
        github_json = json.loads(response.read().decode(response.info().get_param("charset") or "utf-8"))

        # get the underlining system and architecture
        system = platform.system()
        if system == "Linux":
            system = "linux" + platform.architecture()[0].replace("bit", '')
        elif system == "Darwin":
            # the driver for OSX is 32 and 64bit
            system = "macos"
        elif system == "Windows":
            system = "win" + platform.architecture()[0].replace("bit", '')

        # find the right driver for the system
        for asset in github_json["assets"]:
            if system in asset["browser_download_url"]:
                # download the driver
                print("Downloading geckodriver...")
                driver_archive = os.path.join(VIRTUALENV_BASE_DIR, "geckodriver.tar.gz")
                response = urlopen(asset["browser_download_url"])
                with open(driver_archive, 'wb') as out:
                    out.write(response.read())

                # extract the driver
                print("Extracting geckodriver...")
                driver_file = "geckodriver"
                with tarfile.open(driver_archive, "r:gz") as archive_file:
                    archive_file.extract(driver_file, path=VIRTUALENV_BASE_DIR)

                # remove the archive
                os.remove(driver_archive)
                # move the driver to the virtualenv bin directory
                print("Installing geckodriver...")
                shutil.move(os.path.join(VIRTUALENV_BASE_DIR, driver_file),
                            os.path.join(VIRTUALENV_BASE_DIR, "bin", driver_file))

                # nothing more to do
                print("...done")
                break

    @classmethod
    def use_browser(cls, browser):
        if browser not in ("chrome", "firefox", "safari"):
            _CommonTargets.exit("No valid webdriver specified! Choose between 'chrome', 'firefox' and 'safari'.", 1)

        # write the config file
        config_text = ("# This file is automatically generated by the Makefile.\n"
                       "# Do not manually edit it!\n"
                       "\n"
                       "WEBDRIVER = \"{webdriver}\"\n".format(webdriver=browser))
        with open(WEBDRIVER_CONF_FILE, 'w') as f:
            f.write(config_text)

        # install the selenium driver for chrome and firefox
        if browser == "chrome":
            cls.__install_chromedriver()
        elif browser == "firefox":
            cls.__install_geckodriver()

    @classmethod
    def execute_target(cls, parser, argument_values, argv_rest):
        if "webdriver" in argument_values:
            cls.use_browser(argument_values["webdriver"])
        else:
            _HelpTarget.execute_target(parser, argument_values, argv_rest)


@cmd("coverage")
@group("Source code management")
@help("Execute coverage on the source code.")
class _CoverageTarget(_Target):
    @arg("app")
    @multiple
    @help("The Django application name to test.")
    class AppName(_Argument):
        pass

    @arg("func-tests")
    @boolean
    @help("Execute the functional tests.")
    class FuncTests(_Argument):
        pass

    @arg("complete-test")
    @boolean
    @help("Run Django application AND functional tests.")
    class CompleteTest(_Argument):
        pass

    @cmd("report")
    @help("Create the coverage report.")
    class Report(_Target):
        @classmethod
        def execute_target(cls, *unused):
            cov = cls.parent_target.load_coverage()
            cov.report()

    @cmd("html")
    @help("Create the coverage report as HTML.")
    class Html(_Target):
        @classmethod
        def execute_target(cls, *unused):
            cov = cls.parent_target.load_coverage()
            cov.html_report()

    @cmd("xml")
    @help("Create the coverage report as XML.")
    class Xml(_Target):
        @classmethod
        def execute_target(cls, *unused):
            cov = cls.parent_target.load_coverage()
            cov.xml_report()

    @cmd("erase")
    @help("Erase a previously created coverage report.")
    class Erase(_Target):
        @classmethod
        def execute_target(cls, *unused):
            cov = cls.parent_target.load_coverage()
            cov.erase()

    @classmethod
    def __initialize_coverage(cls):
        _CommonTargets.activate_virtual_environment()
        from coverage import Coverage
        return Coverage(data_file=COVERAGE_DATA_FILE, config_file=COVERAGE_SETTINGS_FILE,
                        include=[os.path.join(IGUANA_BASE_DIR, '*')])

    @classmethod
    def load_coverage(cls):
        # get coverage
        cov = cls.__initialize_coverage()

        # check if coverage was executed before
        if not os.path.isfile(COVERAGE_DATA_FILE):
            _CommonTargets.exit("No coverage file found! Please perform a coverage run first.", 1)

        # load the coverage file
        cov.load()

        return cov

    @classmethod
    def execute_target(cls, parser, argument_values, argv_rest):
        cov = cls.__initialize_coverage()
        # start the coverage process
        cov._auto_save = True
        cov.start()
        # perform the tests
        argument_values["ign-imp-errs"] = False
        _TestTarget.execute_target(parser, argument_values, argv_rest)


@cmd("css")
@group("Source code management")
@help("Compile the CSS-files with SASSC.")
class _CSSTarget(_Target):
    @classmethod
    def execute_target(cls, *unused):
        _CommonTargets.activate_virtual_environment()
        import sass

        out_css_dir = os.path.join(STATIC_FILES, "css")

        # create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(out_css_dir), exist_ok=True)

        # use python libsass for compiling the sccs files
        # output them to the normal css folder
        sass.compile(dirname=(IGUANA_SCSS_DIR, out_css_dir))


@cmd("list")
@group("Source code management")
@help("List bugs and missing testcases defined in the code.")
class _ListTarget(_Target):
    @cmd("bugs")
    @help("List bugs.")
    class _ListBugsTarget(_Target):
        @classmethod
        def execute_target(cls, *unused):
            subprocess.run('grep --color -n -i -R -H "TODO BUG" --exclude=' + os.path.basename(__file__) + ' *',
                           shell=True, cwd=IGUANA_BASE_DIR)

    @cmd("missing-testcases")
    @help("List missing testcases.")
    class _ListMissingTestcasesTarget(_Target):
        @classmethod
        def execute_target(cls, *unused):
            subprocess.run('grep --color -n -i -R -H "TODO TESTCASE" --exclude=' + os.path.basename(__file__) + ' *',
                           shell=True, cwd=IGUANA_BASE_DIR)


@cmd("add-license")
@group("Source code management")
@help("Add the license header to the source files.")
class _AddLicenseTarget(_Target):
    @classmethod
    def execute_target(cls, *unused):
        subprocess.run([os.path.join(IGUANA_BASE_DIR, "add_header.sh")], cwd=IGUANA_BASE_DIR)


@cmd("new-release")
@group("Source code management")
@help("Tag the current commit as a production release.")
class _NewReleaseTarget(_Target):
    @classmethod
    def execute_target(cls, *unused):
        _CommonTargets.activate_virtual_environment()

        # get the git repository
        from git import Repo
        repo = Repo(BASE_DIR)
        # get only tags that start with 'production-' and sort them descending by their number
        tags = sorted(repo.tags, key=lambda t: t.name.startswith("production-") and int(t.name.split('-')[1]),
                      reverse=True)

        # get the latest tag number
        if not tags:
            latest_tag_number = 0
        else:
            latest_tag_number = int(tags[0].name.split('-')[1])

        # add a new release tag on the master branch
        repo.create_tag("production-" + str(latest_tag_number + 1), ref="master")


@cmd("production")
@group("Main")
@call_after([_SetupVirtualenvTarget, _CSSTarget, _MigrationsTarget.Create, _MigrationsTarget.Apply, _CollectionTarget])
@help("Configure everything to be ready for production.")
class _ProductionTarget(_Target):
    @classmethod
    def execute_target(cls, unused1, argument_values, unused2):
        # write the production settings
        _CommonTargets.save_dev_stage_setting(development=argument_values.get("development", False),
                                              staging=argument_values.get("staging", False))

        # initialize the rest of the settings
        _CommonTargets.initialize_settings()


@cmd("staging")
@group("Main")
@call_after(_ProductionTarget)
@help("Configure everything to be ready for staging.")
class _StagingTarget(_Target):
    @classmethod
    def execute_target(cls, unused1, argument_values, unused2):
        argument_values["staging"] = True


@cmd("development")
@group("Main")
@call_after([_ProductionTarget, _SetWebdriverTarget])
@help("Configure everything to be ready for development.")
class _DevelopmentTarget(_Target):
    @arg("webdriver")
    @default("chrome")
    @help("Specify the webdriver for the development process.")
    class Webdriver(_Argument):
        pass

    @classmethod
    def execute_target(cls, unused1, argument_values, unused2):
        argument_values["development"] = True

        # link the git hooks
        _CommonTargets.link_git_hooks()


def __get_parser_group(parser, target):
    if isinstance(parser, _SubParsersCustom) and \
            target.group and \
            not target.has_parent:
        # check if group already exists
        if target.group in MAIN_TARGET_GROUPS.keys():
            return MAIN_TARGET_GROUPS[target.group]

        # add the new group to the parser
        group = parser.add_parser_group(target.group + ':')
        MAIN_TARGET_GROUPS[target.group] = group
        return group
    else:
        # if no group is specified with the target, just return the parser
        return parser


def __add_target_to_parser(subparser, target):
    group = __get_parser_group(subparser, target)
    target_parser = group.add_parser(target.cmd, action=target, help=target.help, add_help=target.is_help_needed)

    for argument_cls in target.argument_classes:
        if argument_cls.is_required:
            target_parser.add_argument(argument_cls.arg, action=argument_cls, help=argument_cls.help)
        else:
            target_parser.add_argument(argument_cls.arg_short, argument_cls.arg_long, action=argument_cls,
                                       default=argument_cls.default, help=argument_cls.help)

    # add the child targets
    if target.child_targets:
        target_sp = target_parser.add_subparsers(action=_SubParsersCustom)
    for child_target in target.child_targets:
        __add_target_to_parser(target_sp, child_target)

    if target.child_targets or target.argument_classes:
        def sort_actions(elem):
            if isinstance(elem, target):
                return 1
            elif isinstance(elem, _SubParsersCustom):
                return 2
            else:
                return 0

        # sort the actions so the argument and child actions get called before the target actions
        target_parser._actions.sort(key=sort_actions)


# custom git hooks (relative to the BASE_DIR path)
CUSTOM_GIT_HOOKS = [os.path.relpath(os.path.join(CUSTOM_GIT_HOOK_DIR, hook), BASE_DIR)
                    for hook in os.listdir(CUSTOM_GIT_HOOK_DIR)
                    if os.path.isfile(os.path.join(CUSTOM_GIT_HOOK_DIR, hook))]

# list of groups for the main targets
MAIN_TARGET_GROUPS = {}


# run this script
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Makefile for the Iguana project", add_help=False)
    subparser = parser.add_subparsers(action=_SubParsersCustom)

    # special case help target
    __add_target_to_parser(subparser, _HelpTarget)
    _HelpTarget.root_parser = parser

    # get all target classes
    for _, cls in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(cls) and \
                issubclass(cls, _Target) and \
                cls not in [_Target, _HelpTarget]:
            __add_target_to_parser(subparser, cls)

    parser.parse_args(args=None if sys.argv[1:] else ["help"])
