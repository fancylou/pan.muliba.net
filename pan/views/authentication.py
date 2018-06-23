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
            return APIResponse(result=result_error, message=userid).asdict()

    @view_config(route_name='who', request_method='GET', renderer='json')
    def who(self):
        log.info('who is this %s', self.logged_in)
        if self.logged_in is not None:
            user = query_user(self.request, self.logged_in)
            if isinstance(user, User):
                return APIResponse(result=result_ok, data=user.to_dic()).asdict()
            else:
                return APIResponse(result=result_error, message=user).asdict()
        else:
            return APIResponse(result=result_error, message='anonymous').asdict()

