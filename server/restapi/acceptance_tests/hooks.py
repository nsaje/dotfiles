"""
Hooks for REST API acceptance testing.

More info: https://dredd.readthedocs.io/en/latest/hooks-python/

Transaction names can be listed with `dredd restapi/api_blueprint.md dummy --names`
"""

import json

import dredd_hooks as hooks

stash = {}


@hooks.before("Campaign Management > Campaign Budgets > Create a new campaign budget")
@hooks.before("Ad Group Management > Ad Groups > Update ad group details")
def move_dates_into_future(transaction):
    """ Move dates into the future so tests don't fail with '... must be in the future' """
    body = transaction["request"]["body"]
    body = body.replace("2016", "2116")
    transaction["request"]["body"] = body


@hooks.before("Technical Overview > Acquire a new authentication token > Acquire a new authentication token")
def strip_oauth2_body(transaction):
    """ API Blueprint uses Markdown, which appends a newline to a body. """
    transaction["request"]["body"] = transaction["request"]["body"].strip()


@hooks.after("Technical Overview > Acquire a new authentication token > Acquire a new authentication token")
def stash_token(transaction):
    if "real" in transaction:
        parsed_body = json.loads(transaction["real"]["body"])
        if "access_token" in parsed_body:
            stash["access_token"] = parsed_body["access_token"]


@hooks.before_each
def add_authorization_token(transaction):
    if "access_token" in stash:
        transaction["request"]["headers"]["Authorization"] = "Bearer " + stash["access_token"]


# TODO(nsaje): figure out how to mock this
@hooks.before("Ad Group Management > Realtime Statistics > Get realtime statistics for an ad group")
@hooks.before("Campaign Management > Campaigns > Get campaign performance")
@hooks.before("Video Asset Management > Upload Video Assets > Step 1: Create a new video asset > Example 1")
@hooks.before("Video Asset Management > Upload Video Assets > Step 1: Create a new video asset > Example 2")
@hooks.before("Video Asset Management > Upload Video Assets > Step 1: Create a new video asset > Example 3")
@hooks.before(
    "Video Asset Management > Upload Video Assets > Step 2: Upload the video file or VAST using the provided upload URL"
)
@hooks.before("Video Asset Management > Upload Video Assets > Step 3: Check the video asset upload status")
def skip_test(transaction):
    transaction["skip"] = True
