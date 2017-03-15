import functools
import os
import pprint
import sys

import click
import gidgethub

from twisted.internet import reactor, defer, task
from gidgethub.sansio import accept_format
from gidgethub.treq import GitHubAPI

MY_TOKEN = os.environ['GHKEY']
USER_AGENT = "Lukasa"


def synchronize(f):
    """
    A function decorator that takes an async function and wraps it in a
    function that can invoke it synchronously using twisted's task.react. This
    is done to bridge between Twisted and click.
    """
    @functools.wraps(f)
    def inner(*args, **kwargs):
        d = defer.ensureDeferred(f(*args, **kwargs))
        task.react(lambda *args: d)

    return inner


def protection_data():
    """
    Get a dictionary representing the JSON required to protect a branch.
    """
    # TODO: This should be loadable from a YAML config file of some kind.
    return {
        "required_pull_request_reviews": {
            "include_admins": False,
        },
        "required_status_checks": {
            "include_admins": False,  # Enforce required status checks for repository administrators.
            "strict": True,  # Require branches to be up to date before merging.
            "contexts": ["continuous-integration/travis-ci"],  # The list of status checks to require in order to merge into this branch
        },
        "restrictions": {
            "users": [],  # The list of user logins with push access
            "teams": ["contributors"],  # The list of team slugs with push access
        }
    }


class APIClient:
    """
    An object that communicates with the GitHub API.
    """
    def __init__(self):
        self._gh = GitHubAPI(USER_AGENT, oauth_token=MY_TOKEN)

    async def _get_protection_for_branch(self, owner, reponame, branch):
        """
        Given a branch on a repository, determines its protected status.
        """
        return await self._gh.getitem(
            f"/repos/{owner}/{reponame}/branches/{branch}/protection",
            accept=accept_format(version="loki-preview")
        )

    async def _set_branch_protection(self, owner, reponame, branch, status):
        """
        Given a branch on a repository, sets the branch protection status to
        status. Status must be a dictionary.
        """
        return await self._gh.put(
            f"/repos/{owner}/{reponame}/branches/{branch}/protection",
            data=status,
            accept=accept_format(version="loki-preview"),
        )

    async def branch_requires_review(self, owner, reponame, branch):
        """
        Returns whether or not a given branch requires pull request review
        before merging.
        """
        try:
            response = await self._get_protection_for_branch(
                owner, reponame, branch
            )
        except gidgethub.BadRequest:
            return False
        else:
            return "required_pull_request_reviews" in response

    async def protect_branch(self, owner, reponame, branch):
        """
        Protects a given branch.
        """
        protection_status = protection_data()
        await self._set_branch_protection(owner, reponame, branch, protection_status)


@click.group()
def cli():
    pass


@cli.command()
@click.argument('organisation')
@click.argument('repo')
@click.argument('branch')
@synchronize
async def protection(organisation, repo, branch):
    """
    Query the protection status of a branch.
    """
    client = APIClient()

    if await client.branch_requires_review(organisation, repo, branch):
        print(f"{organisation}/{repo}@{branch} requires review")
    else:
        print(f"{organisation}/{repo}@{branch} does not require review")


@cli.command()
@click.argument('organisation')
@click.argument('repo')
@click.argument('branch', nargs=-1)
@synchronize
async def protect(organisation, repo, branch):
    """
    Protect a branch.

    This command sets a branch as protected using the default settings that
    branchmgr provides.
    """
    client = APIClient()
    results = []
    for b in branch:
        d = defer.ensureDeferred(client.protect_branch(organisation, repo, b))
        results.append(d)

    await defer.gatherResults(results, consumeErrors=True)
