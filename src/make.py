"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import argparse
import json
import os
import sys
import textwrap
import shutil
import subprocess


###########
# VARIABLES
###########
BASE = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
# settings file for the Makefile
MAKE_SETTINGS_FILE = os.path.join(BASE, ".makeSettings_py")

# virtualenv settings
VIRTUALENV_BASE = os.path.join(BASE, "virtualenv")

# tools directory
TOOLS = os.path.join(BASE, "tools")

# django settings
DJANGO_BASE = os.path.join(BASE, "src")
DJANGO_SETTINGS = "common.settings"
DJANGO_STATIC = os.path.join(DJANGO_BASE, "common", "static")
DJANGO_SCSS = os.path.join(DJANGO_BASE, "common", "scss")
DJANGO_SETTINGS_FILE = os.path.join(DJANGO_BASE, "common", "settings", "__init__.py")
WEBDRIVER_CONF = os.path.join(DJANGO_BASE, "common", "settings", "webdriver.py")

# git hooks directory
GITHOOKS = os.path.join(BASE, ".git", "hooks")
# custom git hooks (relative to the BASE path)
CUSTOM_GIT_HOOKS = [os.path.relpath(os.path.join(TOOLS, "git-hooks", hook), BASE)
                    for hook in os.listdir(os.path.join(TOOLS, "git-hooks"))
                    if os.path.isfile(os.path.join(os.path.join(TOOLS, "git-hooks"), hook))]


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


# override of argparse._HelpAction
class _HelpTarget(argparse.Action):
    @property
    @classmethod
    def root_parser(cls):
            return cls._root_parser

    @root_parser.setter
    @classmethod
    def root_parser(cls, value):
            cls._root_parser = value

    def __call__(self, parser, *unused):
        # print no help if choices are possible and no choice is made
        choice_made_and_possible = False
        for action in parser._actions:
            if action.choices is not None:
                for choice in action.choices:
                    if str(choice) == sys.argv[-1]:
                        choice_made_and_possible = True
        if choice_made_and_possible:
            return
        # print help if no choice is made at all
        elif parser.prog.endswith(sys.argv[-1]):
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


class _ProductionTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _StagingTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _DevelopmentTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _RunTarget(argparse.Action):
    def __call__(self, *unused):
        # start the server
        _CommonTargets.exec_django_cmd("runserver")


class _CreateAppTarget(argparse.Action):
    def __call__(self, unused1, unused2, values, *unused):
        # create the new django application
        # a change to the Django directory is necessary because of a bug in the current 'startapp [destination]'
        #   implementation
        os.chdir(DJANGO_BASE)
        _CommonTargets.exec_django_cmd("startapp", values, settings=DJANGO_SETTINGS)
        os.chdir(BASE)


class _MigrationsCreateTarget(argparse.Action):
    def __call__(self, *unused):
        _CommonTargets.exec_django_cmd("makemigrations", settings=DJANGO_SETTINGS)


class _MigrationsApplyTarget(argparse.Action):
    def __call__(self, *unused):
        _CommonTargets.exec_django_cmd("migrate", settings=DJANGO_SETTINGS)


class _TestTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _MessagesCreateTarget(argparse.Action):
    def __call__(self, unused1, namespace, *unused):
        _CommonTargets.exec_django_cmd("makemessages", "-l", namespace.lang_code, settings=DJANGO_SETTINGS)


class _MessagesCompileTarget(argparse.Action):
    def __call__(self, *unused):
        _CommonTargets.exec_django_cmd("compilemessages", settings=DJANGO_SETTINGS)


class _SetupVirtualenvTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # check if already a virtual environment is present
        activate_script = os.path.join(VIRTUALENV_BASE, "bin", "activate_this.py")
        if not os.path.isfile(activate_script):
            # create a new environment
            try:
                import virtualenv
            except ImportError as e:
                _CommonTargets.exit(e, 1)

            virtualenv.create_environment(VIRTUALENV_BASE)

        # use the environment now
        _CommonTargets.use_virtual_environment()

        # install the requirements
        _RequirementsInstallTarget.__call__(self, parser, namespace, values, option_string)


class _RequirementsCheckTarget(argparse.Action):
    def __call__(self, *unused):
        _CommonTargets.use_virtual_environment()

        # import piprot
        from piprot import piprot
        # get the requirements file
        requirements_file = _CommonTargets.get_requirements_file()
        # execute piprot
        piprot.main([open(requirements_file, 'r')], outdated=True)


class _RequirementsInstallTarget(argparse.Action):
    def __call__(self, *unused):
        # check which requirements should be installed
        requirements_file = _CommonTargets.get_requirements_file()

        # install the requirements
        _CommonTargets.use_virtual_environment()
        from pip._internal import main as pipmain
        pipmain(["install", "-r", requirements_file])


class _SetWebdriverTarget(argparse.Action):
    def __call__(self, parser, *unused):
        # get the new browser
        new_browser = parser.prog.split(' ')[-1]

        # write the config file
        config_text = ("# This file is automatically generated by the Makefile.\n"
                       "# Do not manually edit it!\n"
                       "\n"
                       "WEBDRIVER = \"{webdriver}\"\n".format(webdriver=new_browser))
        with open(WEBDRIVER_CONF, 'w') as f:
            f.write(config_text)


class _CoverageTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # _CommonTargets.use_virtual_environment()
        # arguments in namespace
        # from coverage import Coverage
        # cov = Coverage()
        # cov.start()
        # run test target
        # cov.stop()
        # cov.save()
        pass


class _CoverageSubTargets(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # cmd in parser.prog
        # cov.load()
        pass


class _CSSTarget(argparse.Action):
    def __call__(self, *unused):
        # check if sassc executable exists
        sassc_file = None
        for path in os.environ["PATH"].split(os.pathsep):
            sassc_file = os.path.join(path, "sassc")
            if os.path.isfile(sassc_file) and os.access(sassc_file, os.X_OK):
                break

        if sassc_file is None:
            print("WARNING: sassc not installed!")
        else:
            # get the SCSS files
            scss_files = [css for css in os.listdir(DJANGO_SCSS)
                          if os.path.isfile(os.path.join(DJANGO_SCSS, css)) and css.endswith(".sccs")]

            # iterate over the SCSS files
            for scss in scss_files:
                out_css_file = os.path.join(DJANGO_STATIC, "css",
                                            os.path.splitext(os.path.basename(scss))[0] + ".css")
                # call sassc
                subprocess.run([sassc_file, scss, out_css_file])


class _ListBugsTarget(argparse.Action):
    def __call__(self, *unused):
        subprocess.run('grep --color -n -i -R -H "TODO BUG" --exclude=' + os.path.basename(__file__) + ' *',
                       shell=True, cwd=DJANGO_BASE)


class _ListMissingTestcasesTarget(argparse.Action):
    def __call__(self, *unused):
        subprocess.run('grep --color -n -i -R -H "TODO TESTCASE" --exclude=' + os.path.basename(__file__) + ' *',
                       shell=True, cwd=DJANGO_BASE)


class _AddLicenseTarget(argparse.Action):
    def __call__(self, *unused):
        subprocess.run([os.path.join(DJANGO_BASE, "add_header.sh")], cwd=DJANGO_BASE)


class _NewReleaseTarget(argparse.Action):
    def __call__(self, *unused):
        _CommonTargets.use_virtual_environment()

        # get the git repository
        from git import Repo
        repo = Repo(BASE)
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


class _ValidateHTMLTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _CommonTargets():
    @classmethod
    def remove_dev_stage_setting(cls):
        # remove the settings file if it exeists
        if os.path.isfile(MAKE_SETTINGS_FILE):
            os.remove(MAKE_SETTINGS_FILE)

    @classmethod
    def remove_virtualenv_directory(cls):
        if os.path.isdir(VIRTUALENV_BASE):
            shutil.rmtree(VIRTUALENV_BASE, ignore_errors=True)

    @classmethod
    def use_virtual_environment(cls):
        # check if already a virtual environment is present
        activate_script = os.path.join(VIRTUALENV_BASE, "bin", "activate_this.py")
        if not os.path.isfile(activate_script):
            cls.exit("No virtual environment is present! Please run 'setup-virtualenv'.", 1)

        # use the environment now
        globs = globals()
        globs.update({
                "__file__": activate_script,
                "__name__": "__main__"
            })
        with open(activate_script, "rb") as f:
            exec(compile(f.read(), activate_script, "exec"), globs)

    @classmethod
    def get_requirements_file(cls):
        # check which requirements should be installed
        settings = cls._get_dev_stage_setting()
        requirements_file = os.path.join(BASE, "requirements")
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
        if os.path.isfile(WEBDRIVER_CONF):
            import common.settings.webdriver as driver
            WEBDRIVER = driver.WEBDRIVER
        else:
            print("Default webdriver 'chrome' is used.")

    @classmethod
    def initialize_settings(cls):
        settings = cls._get_dev_stage_setting()

        with open(DJANGO_SETTINGS_FILE, 'w') as f:
            if settings["development"]:
                f.write("from .local_conf import *")
            else:
                f.write("from .global_conf import *")

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
            # the relative path to the source file
            hook_src = os.path.join(os.path.relpath(BASE, GITHOOKS), hook)
            # the path for the link destination
            hook_dest = os.path.join(GITHOOKS, os.path.basename(hook))
            # create the system link
            os.symlink(hook_src, hook_dest)

    @classmethod
    def exec_django_cmd(cls, cmd, *args, **kwargs):
        cls.use_virtual_environment()

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


# initialize the argument parser
def __create_argparse():
    parser = argparse.ArgumentParser(description="Makefile for the Iguana project", add_help=False)
    subparser = parser.add_subparsers(action=_SubParsersCustom)

    # custom help target to display the help text of all targets
    subparser.add_parser("help", action=_HelpTarget, help="show this help message and exit.", add_help=False)
    _HelpTarget.root_parser = parser

    # the main targets
    main_grp = subparser.add_parser_group("Main:")
    # production target
    main_grp.add_parser("production", action=_ProductionTarget, help="Configure everything to be ready for production.",
                        add_help=False)
    # staging target
    main_grp.add_parser("staging", action=_StagingTarget, help="Configure everything to be ready for staging.",
                        add_help=False)
    # development target
    main_grp.add_parser("development", action=_DevelopmentTarget,
                        help="Configure everything to be ready for development.", add_help=False)

    # the django targets
    django_grp = subparser.add_parser_group("Django management:")
    # run the server locally
    django_grp.add_parser("run", action=_RunTarget, help="Run the Django server locally.", add_help=False)
    # create a new Django application
    createapp_target = django_grp.add_parser("create-app", help="Create a new Django application.")
    createapp_target.add_argument("APP", action=_CreateAppTarget, type=str, help="The name of the new application.")
    # migrations
    migrations_target = django_grp.add_parser("migrations", action=_HelpTarget, help="Manage the Django migrations.")
    migrations_sp = migrations_target.add_subparsers(action=_SubParsersCustom)
    migrations_sp.add_parser("create", action=_MigrationsCreateTarget, help="Create the Django migrations.")
    migrations_sp.add_parser("apply", action=_MigrationsApplyTarget, help="Apply the Django migrations.")
    # test
    test_target = django_grp.add_parser("test", action=_TestTarget, help="Execute the Django tests.")
    test_target.add_argument("-a", "--app", help="The Django application name to test.")
    test_target.add_argument("-f", "--func-tests", action="store_true", help="Execute the functional tests.")
    test_target.add_argument("-i", "--ign-imp-errs", action="store_true",
                             help="Run the Django tests without error-messages from imported packages.")
    # messages
    messages_target = django_grp.add_parser("messages", action=_HelpTarget, help="Manage the Django messages.")
    messages_sp = messages_target.add_subparsers(action=_SubParsersCustom)
    message_create_target = messages_sp.add_parser("create", action=_MessagesCreateTarget,
                                                   help="Create the Django messages.")
    message_create_target.add_argument("-l", "--lang-code", default="en", type=str,
                                       help="The language code for the messages.")
    messages_sp.add_parser("compile", action=_MessagesCompileTarget, help="Compile the Django messages.")

    # the code management targets
    code_grp = subparser.add_parser_group("Source code management:")

    # target for creating the virtualenv
    code_grp.add_parser("setup-virtualenv", action=_SetupVirtualenvTarget,
                        help="Create the virtual environment for Django.")

    # targets for controlling the requirements
    requirement_target = code_grp.add_parser("requirements", action=_HelpTarget,
                                             help="Manage the requirements for this project.")
    requirement_sp = requirement_target.add_subparsers(action=_SubParsersCustom)
    # check the requirements for updates
    requirement_sp.add_parser("check", action=_RequirementsCheckTarget,
                              help="Check if there are any updates of the requirements.")
    # (re)install the requirements
    requirement_sp.add_parser("install", action=_RequirementsInstallTarget, help="(Re-)Install the requirements.")

    # target for setting the webdriver
    set_webdriver_target = code_grp.add_parser("set-webdriver", action=_HelpTarget,
                                               help="Set the browser that should be used for the functional tests.")
    set_webdriver_sp = set_webdriver_target.add_subparsers(action=_SubParsersCustom)
    set_webdriver_sp.add_parser("chrome", action=_SetWebdriverTarget, help="Use Chrome browser for the webdriver.")
    set_webdriver_sp.add_parser("firefox", action=_SetWebdriverTarget, help="Use Firefox browser for the webdriver.")
    set_webdriver_sp.add_parser("safari", action=_SetWebdriverTarget, help="Use Safari browser for the webdriver.")

    # coverage targets
    coverage_target = code_grp.add_parser("coverage", action=_CoverageTarget,
                                          help="Execute coverage on the source code.")
    coverage_target.add_argument("-a", "--app", help="The Django application name to test.")
    coverage_target.add_argument("-f", "--func-tests", action="store_true", help="Execute the functional tests.")
    coverage_sp = coverage_target.add_subparsers(action=_SubParsersCustom)
    coverage_sp.add_parser("report", action=_CoverageSubTargets,
                           help="Create the coverage report.")
    coverage_sp.add_parser("html", action=_CoverageSubTargets,
                           help="Create the coverage report as HTML.")
    coverage_sp.add_parser("xml", action=_CoverageSubTargets,
                           help="Create the coverage report as XML.")
    coverage_sp.add_parser("erase", action=_CoverageSubTargets,
                           help="Erase a previously created coverage report.")

    # compile sassc
    code_grp.add_parser("css", action=_CSSTarget, help="Compile the CSS-files with SASSC.", add_help=False)

    # list bugs and missing testcases
    list_target = code_grp.add_parser("list", action=_HelpTarget, help="")
    list_sp = list_target.add_subparsers(action=_SubParsersCustom)
    list_sp.add_parser("bugs", action=_ListBugsTarget, help="")
    list_sp.add_parser("missing-testcases", action=_ListMissingTestcasesTarget, help="")

    # add license header to source files
    code_grp.add_parser("add-license", action=_AddLicenseTarget,
                        help="Add the license header to the source files.", add_help=False)

    # set as new production release
    code_grp.add_parser("new-release", action=_NewReleaseTarget, help="Tag the current commit as a production release.",
                        add_help=False)

    # validate the HTML files
    code_grp.add_parser("validate-html", action=_ValidateHTMLTarget, help="Validate the HTML files.", add_help=False)

    return parser


# run this script
if __name__ == "__main__":
    parser = __create_argparse()
    parser.parse_args(args=None if sys.argv[1:] else ["help"])
