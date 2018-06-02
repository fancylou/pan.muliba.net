#!/usr/bin/python
# coding:utf-8

import hashlib
import os
import time


def md5hex(word):
    """ MD5加密算法，返回32位小写16进制符号
    """
    if not isinstance(word, str):
        word = str(word)
    word = word.encode('utf-8')
    m = hashlib.md5()
    m.update(word)
    return m.hexdigest()


def md5file(filename):
    """ 大文件分段读取 生成md5
    :param filename:
    :return:
    """

    def read_chunks(fh):
        fh.seek(0)
        chunk = fh.read(8096)
        while chunk:
            yield chunk
            chunk = fh.read(8096)
        else:  # 最后要将游标放回文件开头
            fh.seek(0)

    m = hashlib.md5()
    if isinstance(filename, str) and os.path.exists(filename):
        with open(filename, "rb") as fh:
            for chunk in read_chunks(fh):
                m.update(chunk)
    # 上传的文件缓存 或 已打开的文件流
    elif filename.__class__.__name__ in ["StringIO", "StringO", "TextIOWrapper"]:
        for chunk in read_chunks(filename):
            m.update(chunk)
    else:
        return ""
    return m.hexdigest()


if __name__ == '__main__':
    word = '这是一句话要加密的'
    print('当前时间：', time.time())
    md5 = md5hex(word)
    print('这个md5:', md5, 'md5 len:', len(md5), '时间：', time.time())
    file = '/Users/fancy/dmg/Parallels Desktop 12.2.0-41591.dmg'
    filemd5 = md5file(file)
    print('file md5:', filemd5, ',len:', len(filemd5), '时间：', time.time())



