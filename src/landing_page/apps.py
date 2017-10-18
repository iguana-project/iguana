"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.apps import AppConfig


class LandingPageConfig(AppConfig):
    name = 'landing_page'

    def ready(self):
        from actstream.registry import registry
        from user_management.models import CustomUser
        from issue.models import Issue, Comment
        from project.models import Project
        from sprint.models import Sprint
        # register models for the activity stream
        registry.register(CustomUser, Issue, Project, Comment, Sprint)

        # register the signals
        import landing_page.signals
