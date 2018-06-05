#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pyramid.httpexceptions import HTTPFound
from pyramid.response import Response
from pyramid.view import view_config
from pyramid.security import (
    remember,
    forget,
    )
from sqlalchemy.exc import DBAPIError
from ..models import User

from ..utils.security import (
    check_password
)


@view_config(route_name='login', renderer='../templates/login.jinja2')
def login(request):
    login_url = request.route_url('login')
    referrer = request.url
    if referrer == login_url:
        referrer = '/'  # never use login form itself as came_from
    came_from = request.params.get('came_from', referrer)
    message = ''
    username = ''
    password = ''
    if 'form.submitted' in request.params:
        username = request.params['login']
        password = request.params['password']
        try:
            query = request.dbsession.query(User)
            user = query.filter(User.username == username).first()
            if user is not None:
                if check_password(password, user.password):
                    headers = remember(request, username)
                    return HTTPFound(location=came_from, headers=headers)
                else:
                    message = 'User Password is Error!'
            else:
                message = 'User not exist'
        except DBAPIError:
            return Response('Db error', content_type='text/plain', status=500)
    return dict(
        name='Login',
        message=message,
        url=request.application_url + '/login',
        came_from=came_from,
        login=username,
        password=password,
    )
