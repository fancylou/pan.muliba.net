#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from pyramid.view import view_config
from sqlalchemy import func
from sqlalchemy.exc import DBAPIError

from pan.views.base_action import BaseAction
from ..models import User
from ..utils.security import check_password, hash_password

log = logging.getLogger(__name__)


class Authentication(BaseAction):
    def __init__(self, request):
        super().__init__(request)

    @view_config(route_name='register', request_method='POST', renderer='json')
    def register(self):
        body = self.request.json_body
        username = body['username']
        password = body['password']
        if username is None or username.strip() == '':
            return super().error_response('用户名不能为空！')
        if password is None or password.strip() == '':
            return super().error_response('密码不能为空！')
        try:
            query = self.db_sess.query(User)
            user = query.filter(User.username == username).first()
            if user is not None:
                return super().error_response('用户名已存在！')
            else:
                new_pw = hash_password(password)
                new_user = User(username=username, password=new_pw)
                self.db_sess.add(new_user)
                new_id = self.db_sess.query(func.max(User.id)).one()[0]
                return super().ok_response(dict(userId=new_id))
        except Exception as e:
            log.error('注册出错, %s' % e)
            return super().error_response('注册用户失败！！！')

    @view_config(route_name='login', request_method='POST', renderer='json')
    def login(self):
        body = self.request.json_body
        username = body['username']
        password = body['password']
        user_id = self._authentication(username, password)
        if isinstance(user_id, int):
            log.info('认证成功，user_id:%s', user_id)
            return super().ok_response(dict(token=self.request.create_jwt_token(user_id)))
        else:
            return super().error_response(user_id)

    @view_config(route_name='who', request_method='GET', renderer='json')
    def who(self):
        log.info('who is this %s', self.logged_in)
        if self.logged_in is not None:
            user = self._query_user(self.logged_in)
            if isinstance(user, User):
                return super().ok_response(user.to_dic())
            else:
                return super().error_response(user)
        else:
            return super().anonymous_response()

    @view_config(route_name='update_password', request_method='PUT', renderer='json')
    def change_password(self):
        log.info('who is this %s', self.logged_in)
        if self.logged_in is not None:
            password = self.request.json_body['password']
            if password is None or password.strip() == '':
                return super().error_response('密码不能为空！')
            user = self._query_user(self.logged_in)
            if isinstance(user, User):
                new_pw = hash_password(password)
                self.db_sess.query(User).filter(User.id == self.logged_in).update({User.password: new_pw})
                return super().ok_response(dict(userId=user.id), message='修改密码成功！')
            else:
                return super().error_response(user)
        else:
            return super().anonymous_response()

    def _authentication(self, username, password):
        try:
            query = self.request.dbsession.query(User)
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

    def _query_user(self, user_id):
        try:
            query = self.request.dbsession.query(User)
            user = query.filter(User.id == user_id).first()
            if user is not None:
                return user
            else:
                return '找不到该用户'
        except DBAPIError as e:
            log.error('数据库查询出错 , %s' % e)
            return '用户查询出错！'

