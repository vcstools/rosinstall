#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2009, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


import os
import stat
import struct
import sys
import unittest

import rosinstall.common

class FunctionsTest(unittest.TestCase):

    def test_normabspath(self):
        base = "/foo/bar"
        self.assertEqual("/foo/bar", rosinstall.common.normabspath('.', base))
        self.assertEqual("/foo/bar", rosinstall.common.normabspath('foo/..', base))
        self.assertEqual("/foo/bar", rosinstall.common.normabspath(base, base))
        self.assertEqual("/foo", rosinstall.common.normabspath("/foo", base))
        self.assertEqual("/foo/bar/bim", rosinstall.common.normabspath('bim', base))
        self.assertEqual("/foo", rosinstall.common.normabspath('..', base))

    
    def test_conditional_abspath(self):
        path = "foo"
        self.assertEqual(os.path.normpath(os.path.join(os.getcwd(), path)), rosinstall.common.conditional_abspath(path))
        path = "http://someuri.com"
        self.assertEqual("http://someuri.com", rosinstall.common.conditional_abspath(path))
