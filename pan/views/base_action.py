#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from .view_model import APIResponse

result_ok = 'ok'
result_error = 'error'


class BaseAction:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid
        self.db_sess = request.dbsession

    def anonymous_response(self):
        return self.error_response('anonymous')

    def error_response(self, message):
        return APIResponse(result=result_error, message=message).asdict()

    def ok_response(self, data, message=''):
        return APIResponse(result=result_ok, data=data, message=message).asdict()
