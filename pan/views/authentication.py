#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from pyramid.view import view_config
from sqlalchemy.exc import DBAPIError
from .view_model import APIResponse
from ..models import (
    User
)
from ..utils.security import (
    check_password
)

log = logging.getLogger(__name__)


def authentication(request, username, password):
    try:
        query = request.dbsession.query(User)
        user = query.filter(User.username == username).first()
        if user is not None:
            if check_password(password, user.password):
                return user.id
            else:
                log.info('密码错误, username:%s , password:%s' % (username, password))
                return '密码错误！'
        else:
            log.info('用户名不存在, username:%s , password:%s' % (username, password))
            return '用户名不存在！'
    except DBAPIError as e:
        log.error('数据库查询出错 , %s' % e)
        return '用户查询出错！'


def query_user(request, user_id):
    try:
        query = request.dbsession.query(User)
        user = query.filter(User.id == user_id).first()
        if user is not None:
            return user
        else:
            return '找不到该用户'
    except DBAPIError as e:
        log.error('数据库查询出错 , %s' % e)
        return '用户查询出错！'


result_ok = 'ok'
result_error = 'error'


class Authentication:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid

    @view_config(route_name='login', request_method='POST', renderer='json')
    def login(self):
        request = self.request
        body = request.json_body
        username = body['username']
        password = body['password']
        userid = authentication(request, username, password)
        if isinstance(userid, int):
            log.info('认证成功，user_id:%s', userid)
            return APIResponse(result=result_ok, data=dict(token=request.create_jwt_token(userid))).asdict()
        else:
            return APIResponse(result=result_error, message=userid)

    @view_config(route_name='who', request_method='GET', renderer='json')
    def who(self):
        log.info('who is this %s', self.logged_in)
        if self.logged_in is not None:
            user = query_user(self.request, self.logged_in)
            if isinstance(user, User):
                return APIResponse(result=result_ok, data=user.to_dic()).asdict()
            else:
                return APIResponse(result=result_error, message=user)
        else:
            return APIResponse(result=result_error, message='anonymous')

    # @view_config(route_name='login', renderer='../templates/login.jinja2')
    # def login(self):
    #     request = self.request
    #     login_url = request.route_url('login')
    #     referrer = request.url
    #     if referrer == login_url:
    #         referrer = '/'  # never use login form itself as came_from
    #     came_from = request.params.get('came_from', referrer)
    #     message = ''
    #     username = ''
    #     password = ''
    #     if 'form.submitted' in request.params:
    #         username = request.params['login']
    #         password = request.params['password']
    #         try:
    #             query = request.dbsession.query(User)
    #             user = query.filter(User.username == username).first()
    #             if user is not None:
    #                 if check_password(password, user.password):
    #                     headers = remember(request, username)
    #                     return HTTPFound(location=came_from, headers=headers)
    #                 else:
    #                     message = 'User Password is Error!'
    #             else:
    #                 message = 'User not exist'
    #         except DBAPIError:
    #             return Response('Db error', content_type='text/plain', status=500)
    #     return dict(
    #         name='Login',
    #         message=message,
    #         url=request.application_url + '/login',
    #         came_from=came_from,
    #         login=username,
    #         password=password,
    #     )
    #
    # @view_config(route_name='logout')
    # def logout(self):
    #     request = self.request
    #     headers = forget(request)
    #     url = request.route_url('home')
    #     return HTTPFound(location=url,
    #                      headers=headers)
