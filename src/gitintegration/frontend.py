"""
Iguana (c) by Marc Ammon, Moritz Fickenscher, Lukas Fridolin,
Michael Gunselmann, Katrin Raab, Christian Strate

Iguana is licensed under a
Creative Commons Attribution-ShareAlike 4.0 International License.

You should have received a copy of the license along with this
work. If not, see <http://creativecommons.org/licenses/by-sa/4.0/>.
"""
from git import Repo, Git

import os
import re
from django.db import IntegrityError, transaction
from git.exc import BadName, GitCommandError, NoSuchPathError

from .models import Repository, Commit

EMPTY_TREE_SHA = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"


class Frontend():
    def set_auth(repository):
        git_ssh_cmd = 'ssh -i {}'.format(repository.rsa_priv_path.path)
        os.environ['GIT_SSH_COMMAND'] = git_ssh_cmd

    def clone_repository(repository):
        repo_url = repository.url
        repo_path = repository.get_local_repo_path()
        Frontend.set_auth(repository)

        try:
            repo = Repo.clone_from(repository.url, repository.get_local_repo_path(), branch='master')
            repository.conn_ok = True
        except Exception:
            repository.conn_ok = False

        repository.save()

    def import_new_commits(repository):
        repo_path = repository.get_local_repo_path()
        Frontend.set_auth(repository)

        # already checked out?
        if not os.path.isdir(repo_path):
            Frontend.clone_repository(repository)

        repo = None

        try:
            repo = Repo(repo_path)
            repo.git.pull()
            repository.conn_ok = True
        except Exception:
            repository.conn_ok = False
            repository.save()
            return

        # get hexshas limiting commit range to analyze
        master = repo.commit('master').hexsha
        last = repository.last_commit_processed

        iter_str = master
        if last != '':
            # we already processed commits, limit iteration
            iter_str = last + ".." + master

        # set last_commit_processed to master
        repository.last_commit_processed = master
        repository.save()

        # iterate over commits
        for c in repo.iter_commits(iter_str):
            # try to extract issue describer from commit message
            issue_describer = re.match("^" + repository.project.name_short + r"-\d+ ", c.message)
            # skip commit if is doesn't match the form "^<prj-name-short>-<digit> "
            if issue_describer is None:
                continue

            # extract id: split at "-" and strip trailing whitespace
            issue_id = int(issue_describer.group().split("-")[1][:-1])
            matching_issues = repository.project.issue.filter(number=issue_id)

            if matching_issues.count() != 1:
                # we have zero or more matching issues => ignore commit
                continue

            # extract commit message without issue describer
            message = c.message[issue_describer.end():]

            # prepare commit to store (cts)
            cts = Commit()
            cts.issue = matching_issues.first()
            cts.repository = repository
            cts.date = c.authored_datetime
            cts.author = c.author.name
            cts.name = c.hexsha
            cts.message = message
            cts.set_changes(c.stats.files)

            try:
                # NOTE: See http://stackoverflow.com/questions/21458387/
                with transaction.atomic():
                    cts.save()
            except IntegrityError:
                # this might happen if a commit is imported multiple times, just ignore this
                continue

        # build up a dict of all tags
        tags = {}
        for tag in repo.tags:
            tags.setdefault(tag.commit.hexsha, []).append(tag.name)

        # check commits for new tags
        for commit in repository.commits.all():
            try:
                if len(commit.get_tags()) != len(tags[commit.name]):
                    # new tags for commit
                    commit.set_tags(tags[commit.name])
                    commit.save()
            except KeyError:
                # nothing to do here, commit simply has no tags
                pass

    def get_diff(repository, sha_commit, filepath):
        repo_path = repository.get_local_repo_path()
        Frontend.set_auth(repository)

        repo = None
        commit = None
        parent = None
        diff = None

        try:
            repo = Repo(repo_path)
        except NoSuchPathError:
            repository.conn_ok = False
            repository.save()
            return ""

        try:
            commit = repo.commit(sha_commit)
        except BadName:
            return ""

        if not commit.parents:
            # first commit, use EMPTY_TREE_SHA
            parent = EMPTY_TREE_SHA
            # TODO BUG this is broken!!
            return ""
        else:
            # use first parent
            parent = commit.parents[0]

        # find diff object matching filepath
        try:
            diff = next(d for d in parent.diff(commit, create_patch=True) if d.b_path == filepath)
        except StopIteration:
            # element not found
            return ""

        return diff.diff.decode()
