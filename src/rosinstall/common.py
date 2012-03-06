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

import urlparse
import os
from threading import Thread

class MultiProjectException(Exception): pass

def conditional_abspath(uri):
  """
  @param uri: The uri to check
  @return: abspath(uri) if local path otherwise pass through uri
  """
  u = urlparse.urlparse(uri)
  if u.scheme == '': # maybe it's a local file?
    return os.path.abspath(uri)
  else:
    return uri


def normabspath(localname, path):
  """
  if localname is absolute, return it normalized. If relative, return normalized join of path and localname
  """
  if os.path.isabs(localname) or path is None:
    return os.path.realpath(localname)
  abs_path = os.path.realpath(os.path.join(path, localname))
  return abs_path



## Multithreading The following classes help with distributing work
## over several instances, providing wrapping for starting, joining,
## collecting results, and catching Exceptions. Also they provide
## support for running groups of threads sequentially, for the case
## that some library is not thread-safe.
  
class WorkerThread(Thread):
  def __init__(self, worker, outlist, index):
    Thread.__init__(self)
    self.worker = worker
    self.outlist = outlist
    self.index = index

  def run(self):
    result = {'entry': self.worker.element}
    try:
      result_dict = self.worker.do_work()
      if result_dict is not None:
        result.update(result_dict)
      else:
        result.update({'error': "worker returned None"})
    except MultiProjectException as e:
      result.update({'error': e})
    self.outlist[self.index] = result

class ThreadSequentializer(Thread):
  """helper class to run 'threads' one after the other"""
  def __init__(self):
    Thread.__init__(self)
    self.workers = []
  def add_worker(self, worker):
    self.workers.append(worker)
  def run(self):
    for worker in self.workers:
      worker.run() # not calling start on purpose

class DistributedWork():
  def __init__(self, capacity):
    self.outputs=[None for i in range(capacity)]
    self.threads = []
    self.sequentializers = {}
    self.index = 0
  def add_thread(self, worker):
    thread = WorkerThread(worker, self.outputs, self.index)
    if self.index >= len(self.outputs):
      raise MultiProjectException("Bug: Declared capacity exceeded %s >= %s"%(self.index, len(self.outputs)))
    self.index += 1
    self.threads.append(thread)
    
  def add_to_sequential_thread_group(self, worker, group):
    """Workers in each sequential thread group run one after the other, groups run in parallel"""
    thread = WorkerThread(worker, self.outputs, self.index)
    if self.index >= len(self.outputs):
      raise MultiProjectException("Bug: Declared capacity exceeded %s >= %s"%(self.index, len(self.outputs)))
    self.index += 1
    if group not in self.sequentializers:
      self.sequentializers[group] = ThreadSequentializer()
      self.sequentializers[group].add_worker(thread)
      self.threads.append(self.sequentializers[group])
    else:
      self.sequentializers[group].add_worker(thread)
  def run(self):
    for thread in self.threads:
      thread.start()
    running_threads = self.threads
    while len(running_threads) > 0:
      running_threads = [t.join(1) for t in running_threads if t is not None and t.is_alive()]
    self.outputs = filter(lambda x: x is not None, self.outputs)
    message = ''
    for output in self.outputs:
      if "error" in output:
        if 'entry' in output:
          message += "Error during install of %s : %s\n"%(output['entry'].get_path, output["error"])
        else:
          message += "%s\n"%output["error"]
    if message != '':
      raise MultiProjectException()
    return self.outputs
