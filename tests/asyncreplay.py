#!/usr/bin/env python

from tornado import gen
from tornado.ioloop import IOLoop
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPResponse
from tornado.httpclient import HTTPRequest
from tornado.httpclient import HTTPError
import StringIO
import quopri
import json
import hashlib

import mock
import os.path
import logging

from contextlib import contextmanager


logger = logging.getLogger('braspag')


class ReplayRecording(object):
    """
    Holds on to a set of request keys and their response values.
    Can be used to reproduce HTTP/HTTPS responses without using
    the network.
    """
    def __init__(self, jsonable=None):
        self.request_responses = []
        if jsonable:
            self._from_jsonable(jsonable)

    def _from_jsonable(self, jsonable):
        self.request_responses = [(r['body_hash'], r['request'], r['response'])
                                  for r in jsonable]

    def get_body_hash(self, body):
        return '123'
        return str(hashlib.md5(body and body or '').hexdigest())

    def __getitem__(self, request):
        """Match requests by the tuple (url, method)
        """
        body_hash = self.get_body_hash(request.body)
        for (rec_body_hash, rec_request, rec_response) in self.request_responses:
            logger.debug('testing body hash %s -> %s -- url: %s -> %s method: %s -> %s\n' % (body_hash, rec_body_hash, request.url, rec_request['url'],
                     request.method, rec_request['method']))
            if rec_body_hash == body_hash and \
                    rec_request['url'] == request.url and \
                    rec_request['method'] == request.method:
                logger.debug('found it!')
                return rec_response
        else:
            logger.debug('response not found.')
            raise KeyError

    def __contains__(self, request):
        try:
            self[request]
        except:
            return False
        else:
            return True

    def __setitem__(self, request, response):
        self.request_responses.append((self.get_body_hash(request.body), request, response))

    def to_jsonable(self):
        return [dict(
            body_hash=body_hash,
            request=request,
            response=response) for body_hash, request, response in self.request_responses]

    def to_httpresponse(self, request):
        """Try and get a response that matches the request, create a HTTPResponse
        object from it and return it.
        """
        response_dict = self[request]
        return HTTPResponse(
            request,
            response_dict['status']['code'],
            headers=response_dict['headers'],
            buffer=StringIO.StringIO(response_dict['body']),
            reason=response_dict['status']['message'])


class ReplayRecordingManager(object):
    """
    Loads and saves replay recordings as to json files.
    """
    @classmethod
    def load(cls, recording_file_name):
        try:
            with open(recording_file_name) as fp:
                recording = ReplayRecording(json.load(fp))
        except IOError:
            logger.debug("ReplayRecordingManager starting new %r",
                     os.path.basename(recording_file_name))
            recording = ReplayRecording()
        else:
            logger.debug("ReplayRecordingManager loaded from %r",
                     os.path.basename(recording_file_name))
        return recording

    @classmethod
    def save(cls, recording, recording_file_name):
        logger.debug("ReplayRecordingManager saving to %r",
                 os.path.basename(recording_file_name))
        dirname, _ = os.path.split(recording_file_name)
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        with open(recording_file_name, 'w') as recording_file:
            json.dump(
                recording.to_jsonable(),
                recording_file,
                indent=4,
                sort_keys=True,
                cls=RequestResponseEncoder)


class RequestResponseEncoder(json.JSONEncoder):
    """Encoder that handles HTTPRequest and HTTPResponse objects.
    """
    def default(self, obj):
        if isinstance(obj, HTTPRequest):
            return {
                'url': obj.url,
                'method': obj.method,
                'body': obj.body,
                'user_agent': obj.user_agent,
                'headers': obj.headers
            }
        if isinstance(obj, HTTPResponse):
            return {
                'headers': obj.headers,
                'status': {'code': obj.code, 'message': obj.reason},
                'body': obj.body,
                'body_quoted_printable': quopri.encodestring(obj.body)
            }

        return json.JSONEncoder.default(self, obj)


def async_replay_patch(fetch_mock, recordfile):
    @gen.coroutine
    def side_effect(request, **kwargs):
        """Replay http requests for all hosts except localhost.
        """
        if not isinstance(request, HTTPRequest):
            request = HTTPRequest(request, **kwargs)

        skip_url_start = ['http://localhost', 'https://localhost']
        if any([request.url.startswith(s) for s in skip_url_start]):
            logger.debug('Skipping recording requests to localhost. URL: {0}'.format(request.url))
            try:
                response = yield AsyncHTTPClient(force_instance=True).fetch(request)
            except HTTPError as e:
                response = e.response
            raise gen.Return(response)

        recording = ReplayRecordingManager.load(recordfile)
        if request in recording:
            try:
                response = recording.to_httpresponse(request)
            except Exception as e:
                logger.debug('Found recorded response, but cant parse it. Returning None.')
                raise gen.Return(None)
            else:
                raise gen.Return(recording.to_httpresponse(request))

        logger.debug('Response not found in recording.')

        client = AsyncHTTPClient(force_instance=True)
        try:
            response = yield client.fetch(request)
        except HTTPError as e:
            response = e.response

        recording[request] = response
        ReplayRecordingManager.save(recording, recordfile)

        raise gen.Return(response)

    fetch_mock.side_effect = side_effect


@contextmanager
def asyncreplay(recordfile):
    with mock.patch.object(AsyncHTTPClient(), 'fetch') as fetch_mock:
        async_replay_patch(fetch_mock, recordfile)
        yield


@gen.coroutine
def main():
    with asyncreplay(os.path.join(os.getcwd(), 'record-asyncreplay.json')):
        client = AsyncHTTPClient()
        yield client.fetch('http://localhost:8888/')
        yield client.fetch('http://localhost:8888/foobar')


if __name__ == '__main__':
    IOLoop.instance().run_sync(main)
