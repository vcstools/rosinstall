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

import rosdistro
from rosdistro.manifest_provider import get_release_tag
from rospkg import distro as rospkg_distro
import yaml
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

BRANCH_RELEASE = 'release'
BRANCH_DEVEL = 'devel'


class InvalidData(Exception):
    pass


def build_rosinstall(repo_name, uri, vcs_type, version, prefix):
    """
    Build a rosinstall file given some basic information
    """
    rosinstall = []
    repo_name = repo_name if not prefix else '/'.join([prefix, repo_name])

    if version:
        rosinstall.append({vcs_type: {'local-name': repo_name,
                          'uri': uri, 'version': version}})
    else:
        rosinstall.append({vcs_type: {'local-name': repo_name, 'uri': uri}})
    # return yaml.dump(rosinstall, default_flow_style=False)
    return rosinstall


def get_wet_info(wet_distro, name):
    """
    Get information about wet packages or stacks
    """
    repos = wet_distro['repositories']
    for repo in repos:
        info = repos[repo]
        if repo == name or name in info.get('packages', []):
            return (repo, info)
    return None


def get_dry_info(dry_distro, name):
    """
    Get information about dry stacks
    """
    dry_stacks = dry_distro.get_stacks(True)
    if name in dry_stacks:
        stack = dry_stacks[name]
        if stack.vcs_config.type == 'svn':
            return (name,
                    stack.vcs_config.release_tag, stack.vcs_config.type, None)
        else:
            return (name,
                    stack.vcs_config.anon_repo_uri, stack.vcs_config.type,
                    stack.vcs_config.release_tag)
    return None


def get_release_rosinstall(name, wet_distro, dry_distro, prefix):
    """
    Check if the name is in the wet distro
    """
    info = get_wet_info(wet_distro, name)
    if info:
        repo_name, repo_info = info
        if repo_name == name and 'packages' in repo_info:
            rosinstall = []
            pkg_prefix = '/'.join([prefix, repo_name]) if prefix else repo_name
            for pkg in repo_info['packages'].keys():
                rosinstall.extend(build_rosinstall(pkg, repo_info['url'], 'git', '/'.join(
                    ['release', pkg, repo_info['version'].split('-')[0]]), pkg_prefix))
            return rosinstall
        else:
            return build_rosinstall(
                name,
                repo_info['url'],
                'git',
                '/'.join(['release', name, repo_info['version'].split('-')[0]]),
                prefix)

    # Check if the name is in the dry distro
    info = get_dry_info(dry_distro, name)
    if info:
        name, uri, vcs_type, version = info
        return build_rosinstall(name, uri, vcs_type, version, prefix)

    return None


def get_manifest_yaml(name, distro):
    # If we didn't find the name, we need to try to find a stack for it
    url = 'http://ros.org/doc/%s/api/%s/manifest.yaml' % (distro, name)
    try:
        return yaml.load(urlopen(url))
    except:
        raise IOError("Could not load a documentation manifest for %s-%s from ros.org\n\
Have you selected a valid distro? Did you spell everything correctly? Is your package indexed on ros.org?\n\
I'm looking here: %s for a yaml file." % (distro, name, url))


def _get_fuerte_release():
    """
    Please delete me when fuerte is not supported anymore
    See REP137 about rosdistro files
    """
    url = 'https://raw.github.com/ros/rosdistro/master/releases/fuerte.yaml'
    try:
        fuerte_distro = yaml.load(urlopen(url))
    except:
        raise IOError("Could not load the fuerte rosdistro file from github.\n"
                      "Are you sure you've selected a valid distro?\n"
                      "I'm looking for the following file %s" % url)
    return fuerte_distro


def _get_fuerte_rosinstall(name, prefix=None):
    """
    Please delete me when fuerte is not supported anymore
    See REP137 about rosdistro files
    """
    dry_distro = rospkg_distro.load_distro(rospkg_distro.distro_uri('fuerte'))
    wet_distro = _get_fuerte_release()
    # Check to see if the name just exists in one of our rosdistro files
    rosinstall = get_release_rosinstall(name, wet_distro, dry_distro, prefix)
    if rosinstall:
        return rosinstall

    # If we didn't find the name, we need to try to find a stack for it
    doc_yaml = get_manifest_yaml(name, 'fuerte')
    for metapackage in doc_yaml.get('metapackages', []):
        meta_yaml = get_manifest_yaml(metapackage, 'fuerte')
        if meta_yaml['package_type'] == 'stack':
            rosinstall = get_release_rosinstall(
                metapackage, wet_distro, dry_distro, prefix)
            if rosinstall:
                return rosinstall

    return None

def _get_electric_rosinstall(name, prefix=None):
    """
    Please delete me when you don't care at all about electric anymore
    """
    dry_distro = rospkg_distro.load_distro(rospkg_distro.distro_uri('electric'))

    if _is_dry(dry_distro, name):
        return get_dry_rosinstall(dry_distro, name, prefix=prefix)

    # If we didn't find the name, we need to try to find a stack for it
    doc_yaml = get_manifest_yaml(name, 'electric')
    for metapackage in doc_yaml.get('metapackages', []):
        meta_yaml = get_manifest_yaml(metapackage, 'electric')
        if meta_yaml['package_type'] == 'stack':
            if _is_dry(dry_distro, metapackage):
                return get_dry_rosinstall(dry_distro, metapackage, prefix=prefix)

    return None


def _get_rosdistro_release(distro):
    index = rosdistro.get_index(rosdistro.get_index_url())
    return rosdistro.get_distribution_file(index, distro)


def _find_repo(release_file, name):
    for r in release_file.repositories:
        repo = release_file.repositories[r]
        if name in repo.package_names:
            return repo
    return None


def _is_wet(release_file, name):
    return _find_repo(release_file, name) is not None


def _is_dry(dry_distro, name):
    return get_dry_info(dry_distro, name) is not None


def get_wet_rosinstall(release_file, name, prefix=None):
    repo = _find_repo(release_file, name)
    if repo is None:  # wait, what?
        return None
    return build_rosinstall(name, repo.url, 'git', get_release_tag(repo, name), prefix)


def get_dry_rosinstall(dry_distro, name, prefix=None):
    info = get_dry_info(dry_distro, name)
    if info:
        name, uri, vcs_type, version = info
        return build_rosinstall(name, uri, vcs_type, version, prefix)
    return None


def get_release_info(name, distro, prefix=None):
    """
    Steps to check for a released version of the package
    1) Look in the wet distro file for the package/stack name, if it's there, return the repo
    2) Look in the dry distro file for the package/stack name, if it's there, return the repo
    3) Look in the manifest.yaml generated by the documentation indexer to take a best guess at
    what stack a given package belongs to
    4) Look in the distro files again to see if the stack name is there, if it is, return the repo
    """

    # fuerte is different.
    if distro == 'fuerte':
        return _get_fuerte_rosinstall(name, prefix=prefix)

    # electric is ancient.
    if distro == 'electric':
        return _get_electric_rosinstall(name, prefix=prefix)

    wet_distro = _get_rosdistro_release(distro)
    dry_distro = rospkg_distro.load_distro(rospkg_distro.distro_uri(distro))

    # Check to see if the name just exists in one of our rosdistro files
    if _is_wet(wet_distro, name):
        return get_wet_rosinstall(wet_distro, name, prefix=prefix)
    if _is_dry(dry_distro, name):
        return get_dry_rosinstall(dry_distro, name, prefix=prefix)

    # If we didn't find the name, we need to try to find a stack for it
    doc_yaml = get_manifest_yaml(name, distro)
    for metapackage in doc_yaml.get('metapackages', []):
        meta_yaml = get_manifest_yaml(metapackage, distro)
        if meta_yaml['package_type'] == 'stack':
            if _is_dry(dry_distro, metapackage):
                return get_dry_rosinstall(dry_distro, metapackage, prefix=prefix)

    return None


def get_doc_info(name, distro, prefix=None):
    doc_yaml = get_manifest_yaml(name, distro)
    return build_rosinstall(
        doc_yaml['repo_name'], doc_yaml['vcs_uri'], doc_yaml['vcs'],
        doc_yaml.get('vcs_version', ''), prefix)


def get_doc_type(name, distro):
    return get_manifest_yaml(name, distro)['package_type']


def get_doc_www(name, distro):
    return get_manifest_yaml(name, distro)['url']


def get_doc_description(name, distro):
    return get_manifest_yaml(name, distro)['description']
