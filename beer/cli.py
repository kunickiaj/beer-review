# -*- coding: utf-8 -*-
from beer.process import Brewery
import click
import os
import git

pass_brewery = click.make_pass_decorator(Brewery)


@click.group()
@click.option('--config', '-c', default=os.path.expanduser('~/.config/beer-review/beer-review.conf'))
@click.pass_context
def main(ctx, config):
    """CLI for managing your JIRA / Gerrit / git workflow."""
    try:
        repo = git.Repo(os.path.curdir)
    except git.InvalidGitRepositoryError as e:
        click.echo('Current directory is not a git repo!')
        return -1

    repo
    ctx.obj = Brewery(config_file_path=config, repo=repo)


@main.command('brew')
@click.argument('issue_id', required=False, default=None)
@click.option('--issue-type', '-t', default='Bug')
@click.option('--summary', '-s', default=None)
@click.option('--description', '-d', default=None)
@pass_brewery
def init_jira(ctx, issue_id, issue_type, summary, description):
    description = summary if description is None else description
    ctx.work_on(issue_id, issue_type, summary, description)


@main.group('project')
def project():
    """Commands for the project resource."""


@project.command('list')
@pass_brewery
def project_list(ctx):
    """Lists available projects."""
    ctx.list_projects()


