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
from rosinstall.common import MultiProjectException

class FooThing:
    def __init__(self, el, result = None):
        self.element = el
        self.done = False
        self.result = result
    def do_work(self):
        self.done = True
        return self.result
    def get_path_spec(self):
        return self.element
    def get_local_name(self):
        return 'bar'

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


    def test_abspath_overlap(self):
        base = "/foo/bar"
        # simple
        self.assertTrue(rosinstall.common.abspaths_overlap("/foo", "/foo"))
        self.assertTrue(rosinstall.common.abspaths_overlap("/", "/"))
        # denormalized
        self.assertTrue(rosinstall.common.abspaths_overlap("/foo/.", "/foo/bar/../"))
        # subdir
        self.assertTrue(rosinstall.common.abspaths_overlap("/foo", "/foo/bar/baz/bam"))
        ## Negatives
        # simple
        self.assertFalse(rosinstall.common.abspaths_overlap("/foo", "/bar"))
        self.assertFalse(rosinstall.common.abspaths_overlap("/foo", "/foo2"))
        self.assertFalse(rosinstall.common.abspaths_overlap("/foo/bar", "/foo/ba"))

    def test_worker_thread(self):
        try:
            w = rosinstall.common.WorkerThread(None, None, None)
            self.fail("expected Exception")
        except MultiProjectException: pass
        try:
            w = rosinstall.common.WorkerThread(FooThing(el = None), 2, 3)
            self.fail("expected Exception")
        except MultiProjectException: pass
        thing = FooThing(FooThing(None))
        result = [None]
        w = rosinstall.common.WorkerThread(thing, result, 0)
        self.assertEqual(thing.done, False)
        w.run()
        self.assertEqual(thing.done, True, result)
        self.assertEqual(True, 'error' in result[0])
        
        thing = FooThing(FooThing(None), result= {'done': True})
        result = [None]
        w = rosinstall.common.WorkerThread(thing, result, 0)
        self.assertEqual(thing.done, False)
        w.run()
        self.assertEqual(thing.done, True, result)
        self.assertEqual(False, 'error' in result[0], result)
        
    def test_distributed_work(self):
        work = rosinstall.common.DistributedWork(3)
        
        thing1 = FooThing(FooThing(FooThing(None)), result= {'done': True})
        thing2 = FooThing(FooThing(FooThing(None)), result= {'done': True})
        thing3 = FooThing(FooThing(FooThing(None)), result= {'done': True})
        self.assertEqual(3, len(work.outputs))
        work.add_thread(thing1)
        self.assertEqual(1, len(work.threads))
        work.add_thread(thing2)
        self.assertEqual(2, len(work.threads))
        work.add_thread(thing3)
        self.assertEqual(3, len(work.threads))
        self.assertEqual(thing1.done, False)
        self.assertEqual(thing2.done, False)
        self.assertEqual(thing3.done, False)
        output = work.run()
        self.assertEqual(False, 'error' in output[0], output)
        self.assertEqual(False, 'error' in output[1], output)
        self.assertEqual(False, 'error' in output[2], output)
