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
from actstream.actions import follow, unfollow
from django.core.cache import cache
from common.tasks import update_activity_stream_for_user


def follow_project(user, project):
    # follow the project
    follow(user, project, send_action=False, actor_only=False)
    # and all issues of this project
    for issue in project.issue.not_archived():
        follow_issue(user, issue)

    update_activity_stream_for_user.delay(user.username)
    update_activity_stream_for_user.delay(user.username, actor=True)


def unfollow_project(user, project):
    # unfollow the project
    unfollow(user, project)

    # and all of its issues
    for issue in project.issue.not_archived():
        unfollow_issue(user, issue)

    update_activity_stream_for_user.delay(user.username)
    update_activity_stream_for_user.delay(user.username, actor=True)


def follow_issue(user, issue):
    # follow an issue
    follow(user, issue, send_action=False, actor_only=False)


def unfollow_issue(user, issue):
    # unfollow an issue
    unfollow(user, issue)
