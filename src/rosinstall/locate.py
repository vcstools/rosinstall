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

from catkin_pkg.package import parse_package_string
from rosdistro import get_cached_distribution, get_index, get_index_url

BRANCH_RELEASE = 'release'
BRANCH_DEVEL = 'devel'


class InvalidData(Exception):
    pass

def _get_rosinstall_dict(name, data, type_, branch=None, prefix=None):
    """
    From the dict that was read from the online indexer, create a
    single rosinstall dict.
    """
    # This function takes into account that the way VCS
    # information was colleted by the indexer has varied a lot
    # historically (without documentation or announcement thereof), so
    # it's a mess.
    ri_entry = None
    if branch:
        branch_data = data.get('rosinstalls', None)
        if branch_data:
            ri_entry = branch_data.get(branch, None)
        else:
            sys.stderr.write(
                'Warning: No specific branch data for branch "%s" found, falling back on default checkout\n' % branch)

    # if we were unable to compute the rosinstall info based on a
    # desired branch, use the default info instead
    if ri_entry is None:
        prepared_rosinstall = data.get('rosinstall', None)
        if prepared_rosinstall:
            ri_entry = prepared_rosinstall
        else:
            vcs = get_vcs(name, data, type_)
            vcs_uri = get_vcs_uri(data)
            if not vcs or not vcs_uri:
                raise InvalidData(
                    "Missing VCS control information for %s %s, requires vcs[%s] and vcs_uri[%s]" % (type_, name, vcs, vcs_uri))
            vcs_version = get_vcs_version(data)

            ri_entry = {vcs: {'uri': vcs_uri, 'local-name': name } }

            if vcs_version:
                ri_entry[vcs]['version'] = vcs_version

    if prefix:
        prefix = prefix or ''
        for _, v in ri_entry.items():
            if 'local-name' in v:
                local_name = v['local-name']
                # 3513
                # compute path: we can't use os.path.join because rosinstall paths
                # are always Unix-style.
                paths = [x for x in (prefix, local_name) if x]
                path = '/'.join(paths)
                v['local-name'] = path
    return ri_entry


def get_rosinstall(name, data, type_, branch=None, prefix=None):
    """
    Compute a rosinstall fragment for checkout

    @param name: resource name
    @param data: manifest data for resource
    @param branch: source branch type ('devel' or 'release')
    @param prefix: checkout filepath prefix
    @raise InvalidData
    """
    ri_entry = _get_rosinstall_dict(name, data, type_, branch, prefix)
    return yaml.dump([ri_entry], default_flow_style=False)


def get_vcs_uri_for_branch(data, branch=None):
    """
    @param data: rosdoc manifest data
    @param branch: source branch type ('devel' or 'release')
    """
    ri_entry = None
    if branch:
        branch_data = data.get('rosinstalls', None)
        if branch_data:
            ri_entry = branch_data.get(branch, None)
            vcs_type = list(ri_entry.keys())[0]
            return ri_entry[vcs_type]['uri']
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
    return data.get('repo_name', '')


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


def get_manifest(stackage_name, distro_name=None):
    """
    Get the repository and manifest data.

    @param stackage_name: name of package/stack to get manifest information for.
    get_manifest() gives stacks symbols precedence over package
    symbols.
    @type  stackage_name: str
    @param distro_name: name of ROS distribution
    @type  distro_name: str

    @return: (manifest data, 'package'|'stack'|'repository').
    @rtype: ({str: str}, str, str)
    @raise IOError: if data cannot be loaded
    """
    data = None
    if distro_name is not None:
        data = get_manifest_from_rosdistro(stackage_name, distro_name)
    if data is None:
        sys.stderr.write('Not found via rosdistro - falling back to information provided by rosdoc\n')
        data = get_rosdoc_manifest(stackage_name, distro_name)
    return data


def get_manifest_from_rosdistro(package_name, distro_name):
    """
    Get the rosdistro repository data and package information.

    @param package_name: name of package or repository to get manifest information for.
    It gives package symbols precedence over repository names.
    @type  package_name: str
    @param distro_name: name of ROS distribution
    @type  distro_name: str

    @return: (manifest data, 'package'|'repository').
    @rtype: ({str: str}, str, str)
    @raise IOError: if data cannot be loaded
    """
    data = {}
    type_ = None
    index = get_index(get_index_url())
    try:
        distribution_cache = get_cached_distribution(index, distro_name)
    except RuntimeError as runerr:
        if (runerr.message.startswith("Unknown release")):
            return None
        raise

    if package_name in distribution_cache.release_packages:
        pkg = distribution_cache.release_packages[package_name]
        #print('pkg', pkg.name)
        pkg_xml = distribution_cache.get_release_package_xml(package_name)
        pkg_manifest = parse_package_string(pkg_xml)
        data['description'] = pkg_manifest.description
        website_url = [u.url for u in pkg_manifest.urls if u.type == 'website']
        if website_url:
            data['url'] = website_url[0]
        repo_name = pkg.repository_name
        meta_export = [exp for exp in pkg_manifest.exports if exp.tagname == 'metapackage']
        if meta_export:
            type_ = 'metapackage'
        else:
            type_ = 'package'
    else:
        repo_name = package_name
        type_ = 'repository'
    data['repo_name'] = repo_name
    if repo_name in distribution_cache.repositories:
        repo = distribution_cache.repositories[repo_name].release_repository
        if repo:
            data['packages'] = repo.package_names

    if repo_name in distribution_cache.repositories:
        repo = distribution_cache.repositories[repo_name].source_repository
        if not repo:
            return None
        data['vcs'] = repo.type
        data['vcs_uri'] = repo.url
        data['vcs_version'] = repo.version
    else:
        return None

    return (data, type_, None)


def get_rosdoc_manifest(stackage_name, distro_name=None):
    """
    Get the rosdoc manifest data and type of stackage_name.

    @param stackage_name: name of package/stack to get manifest information for.
    get_manifest() gives stacks symbols precedence over package
    symbols.
    @type  stackage_name: str
    @param distro_name: name of ROS distribution
    @type  distro_name: str

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
    url_stack = '%s/api/%s/stack.yaml' % (prefix, stackage_name)
    url_pack = '%s/api/%s/manifest.yaml' % (prefix, stackage_name)
    errors = []
    # ! loop vars used after loop as well
    for type_, url in zip(['stack', 'package'], [url_stack, url_pack]):
        try:
            streamdata = urlopen(url)
            data = yaml.load(streamdata)
            if not data:
                raise InvalidData(
                    'No Information available on %s %s at %s' % (type_,
                                                                 stackage_name,
                                                                 url))
            # with fuerte, stacks also have manifest.yaml, but have a type flag
            realtype = data.get('package_type')
            if realtype:
                type_ = realtype
            break
        except Exception as loope:
            errors.append((url, loope))

    # 1 error is expected when we query package
    if len(errors) > 1:
        error = None
        for (err_url, error) in errors:
            if error is not None:
                sys.stderr.write('error contacting %s:\n%s\n' % (err_url, error))
        raise error
    return (data, type_, url)
