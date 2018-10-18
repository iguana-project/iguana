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
        # print the help
        root_parser = _HelpTarget.root_parser
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


# initialize the argument parser
def __create_argparse():
    parser = argparse.ArgumentParser(description='Makefile for the Iguana project', add_help=False)
    subparser = parser.add_subparsers()

    # custom help target to display the help text of all targets
    help_target = subparser.add_parser("help", help="show this help message and exit.", add_help=False)
    help_target.add_argument('none', action=_HelpTarget, nargs='?', help=argparse.SUPPRESS)
    _HelpTarget.root_parser = parser

    return parser


# run this script
if __name__ == "__main__":
    parser = __create_argparse()
    parser.parse_args(args=None if sys.argv[1:] else ['help'])
