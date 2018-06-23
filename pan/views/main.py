#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import os
import uuid
import shutil
import logging
import time
from .view_model import APIResponse
from pyramid.view import view_config
from sqlalchemy.exc import DBAPIError
from sqlalchemy import func, not_
from ..models import (Folder, File, SourceFile)
from ..utils.md5Helper import md5file
from ..utils.security import (sfid2path, BUCKET, BUCKET_SPLIT)

result_ok = 'ok'
result_error = 'error'
log = logging.getLogger(__name__)


class MainAction:
    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid
        self.db_sess = request.dbsession

    @view_config(route_name='testUpload', renderer='../templates/fileupload.jinja2')
    def test_upload(self):
        settings = self.request.registry.settings
        log.info('read ini file pan.secret: %s' % settings['pan.secret'])
        if 'form.upload' in self.request.params:
            input_file = self.request.POST['file'].file

            file_path = os.path.join('/tmp', '%s.xlsx' % uuid.uuid4())
            log.info('file path %s' % file_path)
            # We first write to a temporary file to prevent incomplete files from
            # being used.
            temp_file_path = file_path + '~'
            log.info('temp file path %s' % temp_file_path)
            # Finally write the data to a temporary file
            input_file.seek(0)
            with open(temp_file_path, 'wb') as output_file:
                shutil.copyfileobj(input_file, output_file)
            # Now that we know the file has been fully saved to disk move it into place.
            os.rename(temp_file_path, file_path)

        return dict(
            message='',
            url=self.request.application_url + '/main/upload',
        )

    @view_config(route_name='upload', renderer='json', request_method='POST')
    def upload(self):
        if self.logged_in is None:
            return self._anonymous_response()
        pid = self.request.POST['pid']
        if pid is None:
            pid = self.request.matchdict["id"]
            if pid is None:
                return self._error_response('传入参数错误，没有pid')
        try:
            settings = self.request.registry.settings
            base_path = settings['pan.base.path']
            log.info('read ini file pan.base.path: %s' % base_path)
            input_file = self.request.POST['file'].file
            if input_file is not None:
                # 获取原始文件名
                filename = self.request.POST['file'].filename
                # 计算扩展名
                extension = os.path.splitext(filename)[-1]
                log.info('extension:%s' % extension)
                # 生成临时文件名
                temp_file_name = (str(uuid.uuid4()) + extension)
                log.info('tmp file :%s' % temp_file_name)
                # 临时文件夹
                tmp_path = '%s/tmp' % base_path
                log.info('tmp path: %s' % tmp_path)
                if os.path.isdir(tmp_path) is False:
                    os.makedirs(tmp_path, exist_ok=True)
                # 临时文件全路径
                tmp_file_path = os.path.join('%s/tmp' % base_path, temp_file_name)
                log.info('temp file path %s' % tmp_file_path)
                # 开始把上传的文件写入临时文件
                input_file.seek(0)
                with open(tmp_file_path, 'wb') as output_file:
                    shutil.copyfileobj(input_file, output_file)
                # 计算md5 真正存储文件
                source_file_id = self._check_storage_file(tmp_file_path, base_path)
                # File对象存储
                if source_file_id is None:
                    return self._error_response('文件存储失败！')
                else:
                    c_time = time.time()
                    new_file = File(pid=pid, uid=self.logged_in, sfId=source_file_id, filename=filename, createTime=c_time, updateTime=c_time)
                    self.db_sess.add(new_file)
                    new_id = self.db_sess.query(func.max(File.id)).one()[0]
                    return APIResponse(result=result_ok, data=dict(fileId=new_id)).asdict()
            else:
                return self._error_response('没有接收到文件')
        except Exception as e:
            log.error('上传文件异常, %s' % e)
            return self._error_response('上传文件异常！')

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
            if pid is None or isinstance(pid, int) is False:
                return self._error_response('文件夹pid不能为空')
            if name is None or name.strip() == '':
                return self._error_response('文件夹名称不能为空')
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

    def _check_storage_file(self, tmp_file_path, base_path):
        try:
            md5_str = md5file(tmp_file_path)
            query_result = self.db_sess.query(SourceFile).filter(SourceFile.md5 == md5_str).first()
            if query_result is not None:
                return query_result.id
            else:
                max_path = self.db_sess.query(func.max(SourceFile.path)).one()[0]
                if max_path is None or max_path == 0:
                    max_path = BUCKET * BUCKET_SPLIT + 1
                else:
                    max_path += 1
                real_path = sfid2path(max_path)
                log.info('计算路径:%s' % real_path)
                tmp_name = os.path.split(tmp_file_path)[1]
                log.info('临时文件名称:%s' % tmp_name)
                extension = os.path.splitext(tmp_file_path)[1]
                log.info('文件扩展：%s' % extension)
                real_absolute_dir = os.path.join(base_path, real_path)
                log.info('最终文件夹:%s' % real_absolute_dir)
                if os.path.isdir(real_absolute_dir) is False:
                    os.makedirs(real_absolute_dir, exist_ok=True)
                real_absolute_path = os.path.join(real_absolute_dir, tmp_name)
                log.info('最终文件全路径：%s' % real_absolute_path)
                shutil.move(tmp_file_path, real_absolute_path)
                file_size = os.path.getsize(real_absolute_path)
                log.info('文件大小：%s' % file_size)
                # 完成文件存储 开始保存数据
                s_file = SourceFile(path=max_path, name=tmp_name, extension=extension, size=file_size, md5=md5_str)
                self.db_sess.add(s_file)
                new_id = self.db_sess.query(func.max(SourceFile.id)).one()[0]
                return new_id
        except Exception as e:
            log.error('存储文件异常， %s' % e)
            return None



