"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.apps import AppConfig
from django.conf import settings


class IssueConfig(AppConfig):
    name = 'issue'

    def ready(self):
        import issue.signals
        from django.contrib.sites.models import Site
        site = Site.objects.get_current()
        site.domain = settings.HOST
        site.name = settings.HOST 
        site.save()
