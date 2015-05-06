# -*- coding: utf-8 -*-
from beer.process import Brewery
import click
import os
import git

pass_beer = click.make_pass_decorator(Brewery)


@click.group()
@click.option('--config', '-c', default=os.path.expanduser('~/.config/beer-review/beer-review.conf'))
@click.option('--session', '-s', default=os.path.expanduser('~/.config/beer-review/jira-session.pickle'))
@click.pass_context
def main(brewery, config, session):
    """CLI for managing your JIRA / Gerrit / git workflow."""
    try:
        repo = git.Repo(os.path.curdir)
    except git.InvalidGitRepositoryError as e:
        click.echo('Current directory is not a git repo!')
        return -1
    brewery.obj = Brewery(config_file_path=config, session_file_path=session, repo=repo)


@main.command('brew',
              help='Work on an existing JIRA or create a new ticket. Not specifying an ISSUE_ID creates a new JIRA.')
@click.argument('issue_id', required=False, default=None)
@click.option('--issue-type', '-t', default='Bug', type=click.Choice(['Bug', 'New Feature', 'Task', 'Improvement']))
@click.option('--summary', '-s', default=None)
@click.option('--description', '-d', default=None, required=False)
@pass_beer
def init_jira(brewery, issue_id, issue_type, summary, description):
    description = summary if description is None else description
    brewery.work_on(issue_id, issue_type, summary, description)


@main.command('taste', help='Post a review or draft to Gerrit.')
@click.option('--draft', '-d', is_flag=True, default=False)
@click.option('--reviewers', '-r', default=None)
@click.option('--target-branch', '-t', default='master')
@pass_beer
def post_review(brewery, draft, reviewers, target_branch):
    brewery.post_review(draft, reviewers, target_branch)


@main.command('drink', help='Submit a review that has been approved +2.')
@pass_beer
def submit(brewery):
    brewery.submit()


@main.group('project')
def project():
    """Commands for the project resource."""


@project.command('list')
@pass_beer
def project_list(brewery):
    """Lists available projects."""
    brewery.list_projects()


