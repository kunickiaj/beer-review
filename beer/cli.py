# -*- coding: utf-8 -*-
import click
from jira.client import JIRA

pass_api = click.make_pass_decorator(JIRA)

@click.group()
@click.option('--user', '-u')
@click.option('--password', '-p')
@click.option('--server', '-s')
@click.pass_context
def main(ctx, user, password, server):
    """CLI for managing your JIRA / Gerrit / git workflow."""
    ctx.obj = JIRA(server=server, basic_auth=(user, password))


@main.group('project')
def project():
    """Commands for the project resource."""


@project.command('list')
@pass_api
def project_list(ctx):
    """Lists available projects."""
    click.echo(ctx.projects())

