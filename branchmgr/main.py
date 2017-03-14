import os
import pprint
import sys

import gidgethub

from twisted.internet import reactor, defer, task
from gidgethub.sansio import accept_format
from gidgethub.treq import GitHubAPI

MY_TOKEN = os.environ['GHKEY']
USER_AGENT = "Lukasa"


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


async def async_main():
    client = APIClient()
    organisation, reponame = sys.argv[1].split('/', 1)
    try:
        branch = sys.argv[2]
    except IndexError:
        branch = sys.argv[2]

    if await client.branch_requires_review(organisation, reponame, branch):
        print(f"{organisation}/{reponame}@{branch} requires review")
    else:
        print(f"{organisation}/{reponame}@{branch} does not require review")


def sync_main(reactor, *args):
    return defer.ensureDeferred(async_main(*args))


def main():
    task.react(sync_main)
