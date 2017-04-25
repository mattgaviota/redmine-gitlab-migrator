from itertools import chain
import re
import requests
import json
from . import APIClient, Project

ANONYMOUS_USER_ID = 2
CLOSED_STATUS = 10 # closed state(Migrada)

class RedmineClient(APIClient):
    PAGE_MAX_SIZE = 100

    def get_auth_headers(self):
        return {"X-Redmine-API-Key": self.api_key}

    def get(self, *args, **kwargs):
        # In detail views, redmine encapsulate "foo" typed objects under a
        # "foo" key on the JSON.
        ret = super().get(*args, **kwargs)
        values = ret.values()
        if len(values) == 1:
            return list(values)[0]
        else:
            return ret

    def unpaginated_get(self, *args, **kwargs):
        """ Iterates over API pagination for a given resource list
        """
        kwargs['params'] = kwargs.get('params', {})
        kwargs['params']['limit'] = 100

        resp = self.get(*args, **kwargs)
        # Try to autofind the top-level key containing
        keys_candidates = (
            set(resp.keys()) - set(['total_count', 'offset', 'limit']))

        assert len(keys_candidates) == 1
        res_list_key = list(keys_candidates)[0]

        result_pages = [resp[res_list_key]]
        if 'offset' not in resp:
            raise ValueError('HTTP response data is not paginated')

        while (resp['total_count'] - resp['offset'] - resp['limit']) > 0:
            kwargs['params']['offset'] = (kwargs['params'].get('offset', 0)
                                          + self.PAGE_MAX_SIZE)
            resp = self.get(*args, **kwargs)
            result_pages.append(resp[res_list_key])
        return chain.from_iterable(result_pages)


class RedmineProject(Project):
    REGEX_PROJECT_URL = re.compile(
        r'^(?P<base_url>https?://.*)/projects/(?P<project_name>[\w_-]+)$')

    REGEX_CATEGORY_PROJECT_URL = re.compile(
        r'^(?P<base_url>https?://.*)/project/(?P<category_name>[\w_-]+)/(?P<project_name>[\w_-]+)/?$')

    def __init__(self, url, *args, **kwargs):
        normalized_url = self._canonicalize_url(url)
        super().__init__(normalized_url, *args, **kwargs)
        self.api_url = '{}.json'.format(self.public_url)
        self.instance_url = self._url_match.group('base_url')

    @classmethod
    def _canonicalize_url(cls, url):
        """ If using caterogies, return the category-less URL

        eg:
          - category URL: https://example.com/project/dev/foobar/
          - category-less URL: https://example.com/projects/foobar/

        API endpoints are reachable only for category-less URLs.
        """
        m = cls.REGEX_CATEGORY_PROJECT_URL.match(url)
        if m:
            return '{base_url}/projects/{project_name}'.format(**m.groupdict())
        else:
            return url

    def get_all_issues(self, closed=False):
        status_ids = ['1']
        if closed:
            status_ids = ['5']
        status_filter = '?status_id={}'.format(*status_ids)

        issues = self.api.unpaginated_get(
            '{}/issues.json{}'.format(self.public_url, status_filter)
        )
        detailed_issues = []
        # It's impossible to get issue history from list view, so get it from
        # detail view...
        for issue_id in (i['id'] for i in issues):
            issue_url = '{}/issues/{}.json?include=journals,relations,childrens,attachments'.format(
                self.instance_url, issue_id)
            detailed_issues.append(self.api.get(issue_url))

        return detailed_issues

    def get_participants(self, closed=False):
        """Get participating users (issues authors/owners)

        :return: list of all users participating on issues
        :rtype: list
        """
        user_ids = set()
        users = []
        # FIXME: cache
        for i in self.get_all_issues(closed):
            for i in chain([i['author'], i.get('assigned_to', None)]):
                if i is None:
                    continue
                user_ids.add(i['id'])

        for i in user_ids:
            # The anonymous user is not really part of the project...
            if i != ANONYMOUS_USER_ID:
                users.append(self.api.get('{}/users/{}.json'.format(
                    self.instance_url, i)))
        return users

    def get_users_index(self, closed=False):
        """ Returns dict index of users (by user id)
        """
        return {i['id']: i for i in self.get_participants(closed)}

    def close_issue(self, data):
        """Update the issue to a closed state"""
        issue_data = """
            <?xml version="1.0" encoding="iso-8859-1"?>
            <issue>
                <status_id>{}</status_id>
                <subject>{} [MIGRADO]</subject>
            </issue>
        """.format(CLOSED_STATUS, data['title'])
        headers = {
            'content-type': 'application/xml',
            'X-Redmine-API-Key': '8d53f0308c5c1ac9ea3d2a50998cea5783cc130e'
        }
        url = '{}/issues/{}.xml'.format(self.instance_url, data['id'])
        return requests.put(
            url,
            data=issue_data.encode('utf-8'),
            headers=headers
        )

    def get_versions(self):
        response = self.api.get('{}/versions.json'.format(self.public_url))
        return response['versions']
