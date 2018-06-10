#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import logging
import time
from .view_model import APIResponse
from pyramid.view import view_config
from sqlalchemy.exc import DBAPIError
from sqlalchemy import func, not_
from ..models import (Folder, File)

result_ok = 'ok'
result_error = 'error'
log = logging.getLogger(__name__)


class MainAction:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid
        self.db_sess = request.dbsession

    @view_config(route_name='top', renderer='json', request_method='GET')
    def top(self):
        log.info('top in coming.....')
        if self.logged_in is not None:
            # 查询当前用户的顶层数据
            top_list = self.db_sess.query(Folder).filter(Folder.pid == '-1', Folder.uid == self.logged_in).all()
            top_dict = []
            for it in top_list:
                top_dict.append(it.to_dic())
            return self._ok_response(top_dict)
        else:
            return self._anonymous_response()

    @view_config(route_name='createFolder', renderer='json', request_method='POST')
    def create_folder(self):
        log.info('create folder in coming.....')
        if self.logged_in is not None:
            body = self.request.json_body
            pid = body['pid']
            name = body['name']
            return self._create_folder_to_db(pid, name)
        else:
            return self._anonymous_response()

    """queryFolder
    """
    @view_config(route_name='queryFolder', renderer='json', request_method='GET')
    def query_folder(self):
        log.info('query folder in coming ...')
        if self.logged_in is not None:
            pid = self.request.matchdict["id"]
            folder_list = self.db_sess.query(Folder).filter(Folder.pid == pid, Folder.uid == self.logged_in).all()
            folder_dict = []
            for it in folder_list:
                folder_dict.append(it.to_dic())
            return self._ok_response(folder_dict)
        else:
            return self._anonymous_response()

    """重命名文件夹 /main/folder/{id}
       """
    @view_config(route_name='renameFolder', renderer='json', request_method='PUT')
    def rename_folder(self):
        log.info('rename folder in coming.....')
        folder_id = self.request.matchdict["id"]
        log.info('rename folder id : %s' % folder_id)
        if self.logged_in is not None:
            body = self.request.json_body
            name = body['name']
            return self._rename_folder_from_db(folder_id, name)
        else:
            return self._anonymous_response()

    """删除文件夹 /main/folder/{id}
    """
    @view_config(route_name='deleteFolder', renderer='json', request_method='DELETE')
    def delete_folder(self):
        log.info('delete folder in coming.....')
        folder_id = self.request.matchdict["id"]
        log.info('delete folder id : %s' % folder_id)
        if self.logged_in is not None:
            return self._delete_folder_from_db(folder_id)
        else:
            return self._anonymous_response()

    def _anonymous_response(self):
        return self._error_response('anonymous')

    def _error_response(self, message):
        return APIResponse(result=result_error, message=message).asdict()

    def _ok_response(self, data):
        return APIResponse(result=result_ok, data=data).asdict()

    def _create_folder_to_db(self, pid, name):
        try:
            folder_query = self.db_sess.query(Folder)
            folder = folder_query.filter(Folder.pid == pid, Folder.name == name, Folder.uid == self.logged_in).first()
            if folder is not None:
                return self._error_response('文件夹重名，name:%s' % name)
            else:
                c_time = time.time()
                folder = Folder(pid=pid, uid=self.logged_in, name=name, createTime=c_time, updateTime=c_time)
                self.db_sess.add(folder)
                new_id = self.db_sess.query(func.max(Folder.id)).one()[0]
                return APIResponse(result=result_ok, data=dict(folderId=new_id)).asdict()
        except DBAPIError as e:
            log.error('保存Folder异常, %s' % e)
            return self._error_response('保存Folder异常')

    def _rename_folder_from_db(self, folder_id, new_folder_name):
        try:
            if folder_id is None:
                return self._error_response('文件夹id不能为空')
            elif new_folder_name is None:
                return self._error_response('文件夹名字不能为空')
            else:
                folder_query = self.db_sess.query(Folder)
                folder = folder_query.filter(Folder.id == folder_id).first()
                dup_name_folder = folder_query.filter(not_(Folder.id == folder.id), Folder.pid == folder.pid,
                                                      Folder.name == new_folder_name).first()
                if dup_name_folder is not None:
                    return self._error_response('文件夹重名，新名字不能使用 %s' % new_folder_name)
                else:
                    update_time = time.time()
                    folder_query.filter(Folder.id == folder_id).update({Folder.name: new_folder_name,
                                                                        Folder.updateTime: update_time})
                    return self._ok_response(dict(folderId=folder_id))
        except DBAPIError as e:
            log.error('重命名Folder异常, %s' % e)
            return self._error_response('重命名Folder异常')

    def _delete_folder_from_db(self, folder_id):
        try:
            if folder_id is None:
                return self._error_response('文件夹id为空')
            else:
                self.db_sess.query(Folder).filter(Folder.id == folder_id).delete()
                return self._ok_response(dict())
        except DBAPIError as e:
            log.error('删除Folder异常, %s' % e)
            return self._error_response('删除Folder异常')
