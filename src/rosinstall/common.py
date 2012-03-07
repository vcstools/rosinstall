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
import copy
# choosing multiprocessing over threading for clean Control-C interrupts (provides terminate())
from multiprocessing import Process, Manager

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

def abspaths_overlap(abspath1, abspath2):
  """
  :returns: True if 2 absolute paths overlap, considering their realpath'
  """
  assert os.path.isabs(abspath1)
  assert os.path.isabs(abspath2)
  realpath1 = os.path.realpath(abspath1)
  realpath2 = os.path.realpath(abspath2)
  if os.path.dirname(realpath1) == os.path.dirname(realpath2):
    return os.path.basename(realpath1) == os.path.basename(realpath2)
  else:
    commonprefix = os.path.commonprefix([realpath1, realpath2])
    return commonprefix == realpath1 or commonprefix == realpath2

def select_element(elements, localname):
  """
  selects entry among elements where path or localname matches.
  Prefers localname matches in case of ambiguity.
  """
  path_candidate = None
  if localname is not None:
    realpath = os.path.realpath(localname)
    for element in elements:
      if localname == element.get_local_name():
        path_candidate = element
        break
      elif realpath == os.path.realpath(element.get_path()):
        path_candidate = element
  return path_candidate

  
## Multithreading The following classes help with distributing work
## over several instances, providing wrapping for starting, joining,
## collecting results, and catching Exceptions. Also they provide
## support for running groups of threads sequentially, for the case
## that some library is not thread-safe.
  
class WorkerThread(Process):

  def __init__(self, worker, outlist, index):
    Process.__init__(self)
    self.worker = worker
    if worker is None or worker.element is None:
      raise MultiProjectException("Bug: Invalid Worker")
    self.outlist = outlist
    self.index = index

  def run(self):
    result = {}
    try:
      result = {'entry': self.worker.element.get_path_spec()}
      result_dict = self.worker.do_work()
      if result_dict is not None:
        result.update(result_dict)
      else:
        result.update({'error': MultiProjectException("worker returned None")})
    except Exception as e:
      result.update({'error': e})
    self.outlist[self.index] = result

class DistributedWork():
  
  def __init__(self, capacity):
    man = Manager() # need managed array since we need the results later
    self.outputs = man.list([None for x in range(capacity)])
    self.threads = []
    self.sequentializers = {}
    self.index = 0
    
  def add_thread(self, worker):
    thread = WorkerThread(worker, self.outputs, self.index)
    if self.index >= len(self.outputs):
      raise MultiProjectException("Bug: Declared capacity exceeded %s >= %s"%(self.index, len(self.outputs)))
    self.index += 1
    self.threads.append(thread)
    
  # def add_to_sequential_thread_group(self, worker, group):
  #   """Workers in each sequential thread group run one after the other, groups run in parallel"""
  #   class ThreadSequentializer(Process):
  #     """helper class to run 'threads' one after the other"""
  #     def __init__(self):
  #       Process.__init__(self)
  #       self.workers = []
  #     def add_worker(self, worker):
  #       self.workers.append(worker)
  #     def run(self):
  #     for worker in self.workers:
  #       worker.run() # not calling start on purpose
  #   thread = WorkerThread(worker, self.outputs, self.index)
  #   if self.index >= len(self.outputs):
  #     raise MultiProjectException("Bug: Declared capacity exceeded %s >= %s"%(self.index, len(self.outputs)))
  #   self.index += 1
  #   if group not in self.sequentializers:
  #     self.sequentializers[group] = ThreadSequentializer()
  #     self.sequentializers[group].add_worker(thread)
  #     self.threads.append(self.sequentializers[group])
  #   else:
  #     self.sequentializers[group].add_worker(thread)
    
  def run(self):
    """
    Execute all collected workers, terminate all on KeyboardInterrupt
    """
    # The following code is rather delicate and may behave differently
    # using threading or multiprocessing. running_threads is
    # intentionally not used as a shrinking list because of al the
    # possible multithreading / interruption corner cases
    try:
      for thread in self.threads:
        thread.start()
      running_threads = self.threads
      while len(running_threads) > 0:
        running_threads = [t for t in self.threads if t is not None and t.is_alive()]
        for thread in running_threads:
          t.join(1)
    except KeyboardInterrupt as k:
      for thread in self.threads:
        if thread is not None and thread.is_alive():
          thread.terminate()
      raise k
    self.outputs = filter(lambda x: x is not None, self.outputs)
    message = ''
    for output in self.outputs:
      if "error" in output:
        if 'entry' in output:
          message += "Error during install of '%s' : %s\n"%(output['entry'].get_local_name(), output["error"])
        else:
          message += "%s\n"%output["error"]
    if message != '':
      raise MultiProjectException(message)
    return self.outputs
