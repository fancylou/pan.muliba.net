#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time;


class APIResponse:
    def __init__(self, result='error', message='', data=dict()):
        self.result = result
        self.message = message
        self.data = data
        self.time = time.time()

    def asdict(self):
        return dict(result=self.result, data=self.data, message=self.message, time=self.time)
