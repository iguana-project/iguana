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
register = template.Library()


# the regex matching of markdown-urlize is not working correctly
# see https://github.com/r0wb0t/markdown-urlize/issues/16
# replace it with a working pattern, thanks to https://mathiasbynens.be/demo/url-regex; thanks @stephenhay
mdx_urlize.URLIZE_RE = r"(%s)" % '|'.join([
    r"\b(?:https?|ftp)://[^\s/$.?#].[^\s]*\b",
    r"\b[^(<\s]+\.(?:com|edu|gov|int|mil|net|org|de)\b"  # use the domains from djangos built-in template tag urlize
])


@register.filter
def markdownify(text):
    """
    Convert a markdown text to HTML.
    """
    return bleach.clean(markdown.markdown(text,
                                          extensions=['markdown.extensions.tables',
                                                      'markdown.extensions.nl2br',
                                                      'markdown.extensions.extra',
                                                      'mdx_urlize',
                                                      ]
                                          ),
                        attributes={u'img': [u'src', u'title', u'height', u'width'],
                                    u'a': [u'href', u'title'],
                                    u'td': [u'align'],
                                    },
                        tags=["p", "b", "a", "i", "img", "ul", "li", "ol", "br", "em",
                              "hr", "h1", "h2", "h3", "h4", "h5", "h6", "pre", "code",
                              "strong", "blockquote", "table", "tr", "td", "th", "thead", "tbody",
                              ]
                        )
