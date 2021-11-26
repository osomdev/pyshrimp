#!/usr/bin/env pyshrimp
# $opts: magic
# $requires: click==7.0,requests==2.22.0
import requests
from click import style

from pyshrimp import log, as_dot_dict


def slog(message, **kwargs):
    log(style(message, **kwargs))


slog('Loading issues...')

res = as_dot_dict(
    requests.get(
        'https://jira.atlassian.com/rest/api/2/search', params={
            'jql': 'created > -1d',
            'maxResults': '5'
        }
    ).json(),
    'res'
)

slog(f'Issues ({res.total} in total):', fg='green', bold=True)
for issue in res.issues:
    line_color = 'red' if issue.fields.issuetype.name == 'Bug' else None
    slog(f' * [{issue.key}] [{issue.fields.issuetype.name}] [{issue.fields.status.name}] {issue.fields.summary}', fg=line_color)
