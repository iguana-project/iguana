"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django import template
import bleach
import markdown
import mdx_urlize
from markdown.inlinepatterns import Pattern
from markdown.extensions import Extension
from project.models import Project
from django.urls.base import reverse
from issue.models import Issue
from builtins import staticmethod
register = template.Library()


# the regex matching of markdown-urlize is not working correctly
# see https://github.com/r0wb0t/markdown-urlize/issues/16
# replace it with a working pattern, thanks to https://mathiasbynens.be/demo/url-regex; thanks @stephenhay
mdx_urlize.URLIZE_RE = r"(%s)" % '|'.join([
    r"\b(?:https?|ftp)://[^\s/$.?#].[^\s]*\b",
    r"\b[^(<\s]+\.(?:com|edu|gov|int|mil|net|org|de)\b"  # use the domains from djangos built-in template tag urlize
])


@register.filter
def markdownify(text, project=None):
    """
    Convert a markdown text to HTML.
    """
    if project and isinstance(project, Project):
        # if the project was specified as parameter, some custom extensions could be loaded
        extra_extensions = [IssueExtension(project),
                            UserExtension(project)]
    else:
        extra_extensions = []

    return bleach.clean(markdown.markdown(text,
                                          extensions=['fenced_code',
                                                      'footnotes',
                                                      'tables',
                                                      'nl2br',
                                                      'mdx_urlize',
                                                      'markdown_del_ins',
                                                      'mdx_truly_sane_lists',
                                                      ] + extra_extensions,
                                          extension_configs={
                                              'mdx_truly_sane_lists': {
                                                  'nested_indent': 4,
                                                  'truly_sane': True,
                                                  }
                                              },
                                          ),
                        attributes={u'img': [u'src', u'title', u'height', u'width'],
                                    u'a': [u'href', u'title'],
                                    u'td': [u'align'],
                                    },
                        tags=["p", "b", "a", "i", "img", "ul", "li", "ol", "br", "em",
                              "hr", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "code",
                              "strong", "blockquote", "table", "tr", "td", "th", "thead", "tbody",
                              "del", "ins", "div", "sup",
                              ]
                        )


class IssueExtension(Extension):
    """
    Resolve and link <project.name_short>-<number> to the right issue.
    """
    class IssuePattern(Pattern):
        def __init__(self, pattern, project, md=None):
            self.project = project
            Pattern.__init__(self, pattern, md=md)

        def handleMatch(self, m):
            issue_short_name = m.group(2)

            number = int(issue_short_name.split('-')[1])
            if number > 0 and \
                    self.project.nextTicketId <= number:
                return issue_short_name
            else:
                issue_object = Issue.objects.get(project=self.project, number=number)
                el = markdown.util.etree.Element("a")
                el.set('href', reverse('issue:detail',
                                       kwargs={'project': self.project.name_short, 'sqn_i': number}))
                el.set("title", markdown.util.AtomicString(issue_object.title))
                el.text = markdown.util.AtomicString(issue_short_name)

                return el

    def __init__(self, project, **kwargs):
        self.project = project
        Extension.__init__(self, **kwargs)

    def extendMarkdown(self, md):
        issue_re_pattern = self.create_issue_pattern(self.project)

        md.inlinePatterns.register(IssueExtension.IssuePattern(issue_re_pattern, self.project, md),
                                   "issuepattern",
                                   100)

    @staticmethod
    def create_issue_pattern(project):
        return r"(\b%s-[0-9]+)" % project.name_short


class UserExtension(Extension):
    """
    Resolve and link @<username> to the right user.
    """
    class UserPattern(Pattern):
        def handleMatch(self, m):
            user_name_with_at = m.group(2)

            el = markdown.util.etree.Element("a")
            el.set('href', reverse('user_profile:user_profile_page',
                                   kwargs={'username': user_name_with_at[1:]}))  # remove the @ character
            el.text = markdown.util.AtomicString(user_name_with_at)

            return el

    def __init__(self, project, **kwargs):
        self.project = project
        Extension.__init__(self, **kwargs)

    def extendMarkdown(self, md):
        user_re_pattern = self.create_user_pattern(self.project)
        md.inlinePatterns.register(UserExtension.UserPattern(user_re_pattern, md),
                                   "userpattern",
                                   100)

    @staticmethod
    def create_user_pattern(project):
        return r"(@%s\b)" % r"\b|@".join([
            user.username for user in project.get_members()
        ])
