#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import bcrypt
import os.path


def hash_password(pw):
    pwhash = bcrypt.hashpw(pw.encode('utf8'), bcrypt.gensalt())
    return pwhash.decode('utf8')


def check_password(pw, hashed_pw):
    expected_hash = hashed_pw.encode('utf8')
    return bcrypt.checkpw(pw.encode('utf8'), expected_hash)


BUCKET = 1024
BUCKET_SPLIT = 1000000


def sfid2path(sfid):
    mask = int(sfid / BUCKET_SPLIT)
    f1 = int(sfid / mask)
    f2 = f1 - BUCKET_SPLIT
    f3 = int(f2 / mask)
    f4 = int(f2 % mask)
    f5 = int(sfid % mask)
    return os.path.join(str(mask), str(f3), str(f4), str(f5))


USERS = {'editor': hash_password('editor'),
         'viewer': hash_password('viewer'),
         'fancy': hash_password('123')}
GROUPS = {'editor': ['group:editors']}


def groupfinder(userid, request):
    if userid in USERS:
        return GROUPS.get(userid, [])


"""{
   "result": "ok",
   "data": {
      "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJzdWIiOjEsImlhdCI6MTUyODUzNTU4Nn0.uUB74qnWDrj__iK9HuqWNamnKnR-tY4vxcdfkHJOmNBL5IN9aAeQzXZghhG2MXC_MIDavWFxETfiJU44Mnfmfw"
   },
   "message": "",
   "time": 1528535586.7144241
}
"""
if __name__ == '__main__':
    # password = 'fancy103'
    # pwhash = hash_password(password)
    # print(pwhash)
    # check = check_password(password, pwhash)
    # print('check result: %s' % check)
    s = sfid2path(1024203002)
    print(s)

