# -*- coding: utf-8 -*-
import click
import ConfigParser
import logging
from jira.client import JIRA
import re
import cPickle as pickle
import os
import subprocess
import urlparse

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)


class Brewery:
    """Workflow Wrapper"""

    def __init__(self, config_file_path, session_file_path, repo=None):
        self._gerrit_url = None
        self._jira = None
        self._repo = repo

        if os.path.isfile(session_file_path):
            with open(session_file_path, 'rb') as session_file:
                session = pickle.load(session_file)
        else:
            session = None

        if config_file_path is not None:
            self._read_config(config_file_path, session)

        if session is not None:
            session.max_retries = 3
            self._jira._session = session
        else:
            with open(session_file_path, 'wb') as session_file:
                pickle.dump(self._jira._session, session_file)

    def _read_config(self, config_file_path, session):
        config = ConfigParser.ConfigParser()
        config.read(config_file_path)

        if len(config.sections()) == 0:
            # New config file
            pass

        # Will terminate if missing configs.
        Brewery._have_required_configs(config)

        self._gerrit_url = urlparse.urlparse(config.get('Gerrit', 'url'), 'ssh')

        if session is not None:
            self._jira = JIRA(server=config.get('JIRA', 'server'))
        else:
            self._jira = JIRA(
                server=config.get('JIRA', 'server'),
                basic_auth=(config.get('JIRA', 'username'), config.get('JIRA', 'password'))
            )

    def work_on(self, issue_id=None, issue_type='Bug', summary=None, description=None):
        if issue_id is not None:
            issue = self._jira.issue(issue_id)
        else:
            issue = self._jira.create_issue(
                project={'key': self._get_project_key()},
                summary=summary,
                description=description,
                issuetype={'name': issue_type}
            )

        issue_id = issue.key
        # Make sure its assigned to you
        self._jira.assign_issue(issue, self._jira.current_user())
        transitions = self._jira.transitions(issue_id)
        # If not already in progress, transition it.
        for transition in transitions:
            if 'Start' in transition['name']:
                self._jira.transition_issue(issue_id, transition['id'])

        if issue_id not in self._repo.heads:
            self._repo.create_head(issue_id)
            self._repo.heads[issue_id].checkout()
            self._repo.index.commit('%s. %s' % (issue_id, issue.fields.summary))
        else:
            self._repo.heads[issue_id].checkout()

    def post_review(self, draft=False, reviewers=None, target_branch='master'):
        ref = 'drafts' if draft else 'for'
        origin = self._repo.remote('origin')
        refspec = 'HEAD:refs/%s/%s' % (ref, target_branch)
        if reviewers is not None:
            refspec = '%s%%r=%s' % (refspec, ",r=".join(reviewers.split(",")))
        res = origin.push(refspec=refspec)
        if len(res) != 1:
            click.echo('Failed to execute git push to post review.')
        else:
            push_info = res[0]
            if push_info.flags & push_info.ERROR != 0:
                click.echo('Failed to post review because %s' % push_info.summary)
            else:
                click.echo('Pushed review for %s. Draft=[%s]' % (self._repo.active_branch.name, draft))

    def submit(self):
        commit_sha = self._repo.active_branch.commit.hexsha
        issue_id = self._repo.active_branch.name
        cmd = [
            'ssh',
            '-p',
            str(self._gerrit_url.port),
            '%s@%s' % (self._gerrit_url.username, self._gerrit_url.hostname),
            'gerrit',
            'review',
            '--submit',
            commit_sha
        ]
        try:
            subprocess.check_call(cmd)

            transitions = self._jira.transitions(issue_id)
            # If not already in progress, transition it.
            for transition in transitions:
                if 'Fixed' in transition['name']:
                    self._jira.transition_issue(issue_id, transition['id'])
        except Exception as e:
            click.echo('Failed to merge review: %s' % e.message)

    def _get_project_key(self):
        head_commit = self._repo.head.commit
        # No match returns None
        match = re.search('^([a-zA-Z]{3})(-[0-9]+)', head_commit.message)
        if match is not None:
            return match.group(1)
        else:
            return None

    @staticmethod
    def _have_required_configs(config):
        """Will raise an exception if any are missing."""
        config.get('JIRA', 'server')
        config.get('JIRA', 'username')
        config.get('JIRA', 'password')
        config.get('Gerrit', 'url')

    def list_projects(self):
        for project in self._jira.projects():
            click.echo('%s - %s' % (project.key, project.name))