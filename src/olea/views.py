"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin, Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under BSD-2-Clause License.

Redistribution and use in source and binary forms, with or without modification,
are permitted provided that the following conditions are met:

   1. Redistributions of source code must retain the above copyright notice,
      this list of conditions and the following disclaimer.
   2. Redistributions in binary form must reproduce the above copyright notice,
      this list of conditions and the following disclaimer
      in the documentation and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect

from lib.custom_model import get_r_object_or_404
from project.models import Project
from sprint.models import Sprint
from olea import parser

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
