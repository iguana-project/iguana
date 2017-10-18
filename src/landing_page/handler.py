"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from actstream import action
from actstream.models import followers
from event import signals
from issue.models import Issue, Comment
from lib.singleton import Singleton
from project.models import Project
from sprint.models import Sprint

from django.core.cache import cache
from common.tasks import update_activity_stream_for_user


class Handler(metaclass=Singleton):
    sender = None
    createVerb = "created"
    modifyVerb = "changed"

    def getTargetObj(self, **kwargs):
        return None

    def handle(self, sender, signal, **kwargs):
        # only add things to the activity stream if there's a user
        if kwargs.get("user", None) is None:
            return

        target = self.getTargetObj(**kwargs)

        # invalidate cache for target followers
        users = followers(target)
        for user in users:
            update_activity_stream_for_user.delay(user.username)
        update_activity_stream_for_user.delay(kwargs['user'].username, actor=True)
        if signal == signals.create:
            action.send(kwargs['user'], verb=self.createVerb, action_object=kwargs['instance'], target=target)
        if signal == signals.modify:
            action.send(kwargs['user'], verb=self.modifyVerb, action_object=kwargs['instance'], target=target)


class ActStreamHandler():
    @classmethod
    def connect_signals(cls):
        for handlerCls in Handler.__subclasses__():
            signals.create.connect(handlerCls.instance.handle, sender=handlerCls.sender)
            signals.modify.connect(handlerCls.instance.handle, sender=handlerCls.sender)

        # special case for the sprint signals
        signals.start.connect(SprintHandler.instance.handle, sender=SprintHandler.sender)
        signals.stop.connect(SprintHandler.instance.handle, sender=SprintHandler.sender)


class IssueHandler(Handler):
    sender = Issue

    def getTargetObj(self, **kwargs):
        return kwargs['instance'].project


class ProjectHandler(Handler):
    sender = Project

    def getTargetObj(self, **kwargs):
        return kwargs['instance']


class CommentHandler(Handler):
    sender = Comment
    createVerb = "added a"

    def getTargetObj(self, **kwargs):
        return kwargs['instance'].issue


class SprintHandler(metaclass=Singleton):
    sender = Sprint
    startVerb = "started"
    stopVerb = "stopped"

    def getTargetObj(self, **kwargs):
        return kwargs['instance'].project

    def handle(self, sender, signal, **kwargs):
        # only add things to the activity stream if there's a user
        if kwargs.get("user", None) is None:
            return

        target = self.getTargetObj(**kwargs)
        if signal == signals.start:
            action.send(kwargs['user'], verb=self.startVerb, action_object=kwargs['instance'], target=target)
        if signal == signals.stop:
            action.send(kwargs['user'], verb=self.stopVerb, action_object=kwargs['instance'], target=target)
