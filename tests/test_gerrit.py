import json

import responses

from bugwarrior.collect import TaskConstructor
from bugwarrior.services.gerrit import GerritService

from .base import ServiceTest, AbstractServiceTest


class TestGerritIssue(AbstractServiceTest, ServiceTest):
    SERVICE_CONFIG = {
        'service': 'gerrit',
        'base_uri': 'https://one.com',
        'username': 'two',
        'password': 'three',
    }

    record = {
        'project': 'nova',
        '_number': 1,
        'branch': 'master',
        'topic': 'test-topic',
        'status': 'new',
        'work_in_progress': False,
        'subject': 'this is a title',
        'messages': [{'author': {'username': 'Iam Author'},
                      'message': 'this is a message',
                      '_revision_number': 1}],
    }

    extra = {
        'annotations': [
            # TODO - test annotations?
        ],
        'url': 'https://one.com/#/c/1/',
    }

    def setUp(self):
        super().setUp()

        responses.add(
            responses.HEAD,
            self.SERVICE_CONFIG['base_uri'] + '/a/',
            headers={'www-authenticate': 'digest'})
        with responses.mock:
            self.service = self.get_mock_service(GerritService)

    def test_to_taskwarrior(self):
        issue = self.service.get_issue_for_record(self.record, self.extra)
        actual = issue.to_taskwarrior()
        expected = {
            'annotations': [],
            'priority': 'M',
            'project': 'nova',
            'gerritid': 1,
            'gerritstatus': 'new',
            'gerritsummary': 'this is a title',
            'gerriturl': 'https://one.com/#/c/1/',
            'gerritbranch': 'master',
            'gerrittopic': 'test-topic',
            'gerritwip': 0,
            'tags': [],
        }

        self.assertEqual(actual, expected)

    def test_work_in_progress(self):
        wip_record = dict(self.record)  # make a copy of the dict
        wip_record['work_in_progress'] = True
        issue = self.service.get_issue_for_record(wip_record, self.extra)

        expected = {
            'annotations': [],
            'description': '(bw)PR#1 - this is a title .. https://one.com/#/c/1/',
            'gerritid': 1,
            'gerritsummary': 'this is a title',
            'gerritstatus': 'new',
            'gerriturl': 'https://one.com/#/c/1/',
            'gerritbranch': 'master',
            'gerrittopic': 'test-topic',
            'gerritwip': 1,
            'priority': 'M',
            'project': 'nova',
            'tags': []}

        self.assertEqual(TaskConstructor(issue).get_taskwarrior_record(), expected)

    @responses.activate
    def test_issues(self):
        self.add_response(
            'https://one.com/a/changes/?q=is:open+is:reviewer&o=MESSAGES&o=DETAILED_ACCOUNTS',
            # The response has some ")]}'" garbage prefixed.
            body=")]}'" + json.dumps([self.record]))

        issue = next(self.service.issues())

        expected = {
            'annotations': ['@Iam Author - is is a message'],
            'description': '(bw)PR#1 - this is a title .. https://one.com/#/c/1/',
            'gerritid': 1,
            'gerritsummary': 'this is a title',
            'gerritstatus': 'new',
            'gerriturl': 'https://one.com/#/c/1/',
            'gerritbranch': 'master',
            'gerrittopic': 'test-topic',
            'gerritwip': 0,
            'priority': 'M',
            'project': 'nova',
            'tags': []}

        self.assertEqual(TaskConstructor(issue).get_taskwarrior_record(), expected)
