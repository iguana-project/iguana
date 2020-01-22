"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect

from lib.custom_model import get_r_object_or_404
from project.models import Project
from sprint.models import Sprint
from issue import parser

# NOTE: ugettext_lazy "is essential when calls to these functions are located in code
#       paths that are executed at module load time."
from django.utils.translation import ugettext as _, ugettext_lazy as _l


# olea short for one line edit add - the functionality to add issues in backlog and board
class ProcessOleaView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        project = get_r_object_or_404(self.request.user, Project, name_short=self.kwargs.get('project'))
        try:
            expression = self.request.POST.get('expression').strip()
            parser.compile(expression, project, self.request.user)

            # add to sprint if currentsprint is set and issue was newly created
            if self.request.POST.get('currentsprint') != "" and parser.issue_created:
                sprint = Sprint.objects.get(project__name_short=self.kwargs.get('project'),
                                            seqnum=self.request.POST.get('currentsprint'))
                parser.issue_to_change.sprint = sprint
                parser.issue_to_change.save()
        except Exception as e:
            messages.add_message(request, messages.ERROR,
                                 _("An error occurred when processing your request") + ": " + str(e))
            # store expression in session data to give edit ability to user
            self.request.session['oleaexpression'] = self.request.POST.get('expression')

        # set focus to olea bar
        self.request.session['oleafocus'] = 'autofocus'

        return redirect(self.request.POST.get('next'))
