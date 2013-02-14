# Software License Agreement (BSD License)
#
# Copyright (c) 2010, Willow Garage, Inc.
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

# Author: kwc

import sys
import yaml
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen
BRANCH_RELEASE = 'release'
BRANCH_DEVEL = 'devel'


class InvalidData(Exception):
    pass


def get_rosinstall(name, data, type_, branch=None, prefix=None):
    """
    Compute a rosinstall fragment for checkout

    @param name: resource name
    @param data: manifest data for resource
    @param branch: source branch type ('devel' or 'release')
    @param prefix: checkout filepath prefix
    @raise InvalidData
    """

    vcs = get_vcs(name, data, type_)
    vcs_uri = get_vcs_uri(data)
    if not vcs and vcs_uri:
        raise InvalidData(
            "Missing VCS control information for %s %s, requires vcs[%s] and vcs_uri[%s]" % (type_, name, vcs, vcs_uri))
    vcs_version = get_vcs_version(data)

    paths = [x for x in (prefix, name) if x]
    path = '/'.join(paths)


    ri_entry = {vcs: {'uri': vcs_uri, 'local-name': path } }

    if vcs_version:
        ri_entry[vcs]['version'] = vcs_version


    return yaml.dump([ri_entry], default_flow_style=False)


def get_vcs_uri_for_branch(data, branch=None):
    """
    @param data: rosdoc manifest data
    @param branch: source branch type ('devel' or 'release')
    """
    ri_entry = None
    if branch and 'rosinstalls' in data:
        ri_entry = data['rosinstalls'].get(branch, None)
        vcs_type = list(ri_entry.keys())[0]
        return ri_entry[vcs_type]['uri']
    else:
        return data.get('vcs_uri', '')


def get_vcs(name, data, type_):
    """
    @param name: resource name
    @param data: rosdoc manifest data
    @param type_: resource type ('stack' or 'package')
    """
    return data.get('vcs', '')

def get_vcs_version(data):
    return data.get('vcs_version', '')

def get_vcs_uri(data):
    return data.get('vcs_uri', '')

def get_repo(name, data, type_):
    """
    @param name: resource name
    @param data: rosdoc manifest data
    @param type_: resource type ('stack' or 'package')
    """
    return data.get('repository', '')


def get_type(data):
    """
    @param data: rosdoc manifest data
    @return 'stack' of 'package'
    """
    return data.get('package_type', 'package')

def get_www(name, data, type_):
    """
    @param name: resource name
    @param data: rosdoc manifest data
    @param type_: resource type ('stack' or 'package')
    """
    return data.get('url', '')


def get_rosdoc_manifest(stackage_name, distro_name=None):
    """
    Get the rosdoc manifest data and type of stackage_name.

    @param stackage_name: name of package/stack to get manifest information for.
    get_manifest() gives stacks symbols precedence over package
    symbols.
    @type  stackage_name: str

    @return: (manifest data, 'package'|'stack').
    @rtype: ({str: str}, str, str)
    @raise IOError: if data cannot be loaded
    """
    ROSDOC_PREFIX = 'http://ros.org/doc'
    if distro_name is not None:
        prefix = '%s/%s' % (ROSDOC_PREFIX, distro_name)
    else:
        prefix = ROSDOC_PREFIX

    data = None

    url = '%s/api/%s/manifest.yaml' % (prefix, stackage_name)
    errors = []

    try:
        streamdata = urlopen(url)
        data = yaml.load(streamdata)
        if not data:
            raise InvalidData(
                'No Information available on %s at %s' % (stackage_name,
                                                          url))
    except Exception as loope:
        errors.append((url, loope))

    # 1 error is expected when we query package
    error = None
    for (err_url, error) in errors:
        if error is not None:
            sys.stderr.write('error contacting %s:\n%s\n' % (err_url, error))
    if error:
        raise error
    type_ = get_type(data)
    return (data, type_, url)
