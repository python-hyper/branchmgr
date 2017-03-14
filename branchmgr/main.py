import json
import os
import pprint
import sys

import gidgethub

from twisted.internet import reactor, defer, task
from gidgethub.sansio import accept_format
from gidgethub.treq import GitHubAPI

MY_TOKEN = os.environ['GHKEY']
USER_AGENT = "Lukasa"


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
        encoded_status = json.dumps(status)
        return await self._gh.put(
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

    async def protect_branch(self, owner, reponame, branch):
        """
        Protects a given branch.
        """
        protection_status = protection_data()
        self._set_branch_protection(owner, reponame, branch, protection_status)


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
