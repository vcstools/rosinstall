import urlparse
import urllib2
import os

__REPOTYPES__ = ['svn', 'bzr', 'hg', 'git']
__ALLTYPES__ = __REPOTYPES__ + ['other', 'setup-file']

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
  if os.path.isabs(localname):
    return  os.path.normpath(localname)
  abs_path = os.path.normpath(os.path.join(path, localname))
  return abs_path

