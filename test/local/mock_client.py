class MockVcsClient():
    """
    Mocked vcs client. TODO: we should be using pathon magic mock instead.
    """
class MockVcsClient():

    def __init__(self,
                 scmtype = 'mocktype',
                 path_exists = False,
                 checkout_success = True,
                 update_success = True,
                 vcs_presence = False,
                 url = "mockurl",
                 actualversion = None,
                 specversion = None):
        self.scmtype = scmtype
        self.path_exists_flag = path_exists
        self.checkout_success = checkout_success
        self.update_success = update_success
        self.vcs_presence = vcs_presence
        self.mockurl = url
        self.checkedout = vcs_presence
        self.updated = False
        self.actualversion = actualversion
        self.specversion = specversion
        
    def get_vcs_type_name(self):
        return self.scmtype

    def get_diff(self, basepath=None):
        return self.scmtype + "mockdiff%s"%basepath

    def get_version(self, revision=None):
        if revision == None:
            return self.actualversion
        else:
            return self.specversion
  
    def get_status(self, basepath=None, untracked=False):
        return self.scmtype + " mockstatus%s,%s"%(basepath, untracked)

    def path_exists(self):
        return self.path_exists_flag

    def checkout(self, uri=None, version=None, verbose=False):
        self.checkedout = True
        return self.checkout_success

    def update(self, version, verbose=False):
        self.updated = True
        return self.update_success

    def detect_presence(self):
        return self.vcs_presence

    def get_url(self):
        return self.mockurl

    def url_matches(self, url, url_or_shortcut):
        return (url == url_or_shortcut or
                url_or_shortcut is None or
                url_or_shortcut.endswith('_shortcut'))
