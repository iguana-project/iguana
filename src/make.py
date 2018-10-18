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

    return parser


# run this script
if __name__ == "__main__":
    parser = __create_argparse()
    parser.parse_args(args=None if sys.argv[1:] else ["help"])
