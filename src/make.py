"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
import argparse
import sys
import textwrap


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
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _CreateAppTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _MigrationsCreateTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _MigrationsApplyTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _TestTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _MessagesCreateTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _MessagesCompileTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _SetupVirtualenvTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _RequirementsCheckTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _RequirementInstallTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _SetWebdriverTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # cmd in parser.prog
        pass


class _CoverageTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # arguments in namespace
        pass


class _CoverageSubTargets(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        # cmd in parser.prog
        pass


class _CSSTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _ListBugsTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _ListMissingTestcasesTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _AddLicenseTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _NewReleaseTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _ValidateHTMLTarget(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        pass


class _CommonTargets():
    pass


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
    createapp_target = django_grp.add_parser("create-app", action=_CreateAppTarget,
                                             help="Create a new Django application.")
    createapp_target.add_argument("APP", help="The name of the new application.")
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
    message_create_target.add_argument("lang-code", default="en", help="The language code for the messages.")
    messages_sp.add_parser("compile", action=_MessagesCompileTarget, help="Compile the Django messages.")

    # the code management targets
    code_grp = subparser.add_parser_group("Source code management:")
    # single subparser for --staging and --development option
    stage_dev_parser = argparse.ArgumentParser(add_help=False)
    stage_dev_parser.add_argument("-s", "--staging", action="store_true", help="Use the settings for staging.")
    stage_dev_parser.add_argument("-d", "--development", action="store_true", help="Use the settings for development.")

    # target for creating the virtualenv
    code_grp.add_parser("setup-virtualenv", action=_SetupVirtualenvTarget, parents=[stage_dev_parser],
                        help="Create the virtual environment for Django.")

    # targets for controlling the requirements
    requirement_target = code_grp.add_parser("requirements", action=_HelpTarget,
                                             help="Manage the requirements for this project.")
    requirement_sp = requirement_target.add_subparsers(action=_SubParsersCustom)
    # check the requirements for updates
    requirement_sp.add_parser("check", action=_RequirementsCheckTarget,
                              help="Check if there are any updates of the requirements.")
    # (re)install the requirements
    requirement_sp.add_parser("install", action=_RequirementInstallTarget, parents=[stage_dev_parser],
                              help="(Re-)Install the requirements.")

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
