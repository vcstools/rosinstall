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
#
# Author: tkruse 



# Programmable completion for the rosws command under bash. Source
# this file (or on some systems add it to ~/.bash_completion and start a new
# shell) and bash's completion mechanism will know all about bzr's options!

SCRIPT_PATH="${BASH_SOURCE[0]}";
if([ -h "${SCRIPT_PATH}" ]) then
  while([ -h "${SCRIPT_PATH}" ]) do SCRIPT_PATH=`readlink "${SCRIPT_PATH}"`; done
fi
export OLDPWDBAK=$OLDPWD
pushd . > /dev/null
cd `dirname ${SCRIPT_PATH}` > /dev/null
SCRIPT_PATH=`pwd`;
popd  > /dev/null
export OLDPWD=$OLDPWDBAK

. $SCRIPT_PATH/rosws.shell

# Based originally on the bzr/svn bash completition scripts.
_rosws_complete()
{
  local cur cmds cmdOpts opt helpCmds optBase i

  COMPREPLY=()
  cur=${COMP_WORDS[COMP_CWORD]}

  cmds='help init install info modify remove diff status snapshot reload switch leave --version'

  if [[ $COMP_CWORD -eq 1 ]] ; then
    COMPREPLY=( $( compgen -W "$cmds" -- $cur ) )
    return 0
  fi

  # if not typing an option, or if the previous option required a
  # parameter, then fallback on ordinary filename expansion
  helpCmds='help|--help|h|\?'
  if [[ ${COMP_WORDS[1]} != @($helpCmds) ]] && \
     [[ "$cur" != -* ]] ; then
    case ${COMP_WORDS[1]} in
    info|diff|status|remove)
      cmdOpts=`rosws info --localnames-only 2> /dev/null | sed -s 's,:, ,g'`
      COMPREPLY=( $( compgen -W "$cmdOpts" -- $cur ) )
    ;;
    modify)
      if [[ ${COMP_WORDS[$(( $COMP_CWORD - 1 ))]} == "--uri" ]]; then
          cmdOpts=`rosws info ${COMP_WORDS[2]} --uri-only 2> /dev/null`
          COMPREPLY=( $( compgen -W "$cmdOpts" -- $cur ) )
      else
          if [[ ${COMP_WORDS[$(( $COMP_CWORD - 1 ))]} == "--version" ]]; then
              cmdOpts=`rosws info ${COMP_WORDS[2]} --version-only 2> /dev/null`
              COMPREPLY=( $( compgen -W "$cmdOpts" -- $cur ) )
          else
              cmdOpts=`rosws info --localnames-only 2> /dev/null | sed -s 's,:, ,g'`
              COMPREPLY=( $( compgen -W "$cmdOpts" -- $cur ) )
          fi
      fi
    ;;
    esac
    return 0
  fi

  cmdOpts=
  case ${COMP_WORDS[1]} in
  status)
    cmdOpts="-h --help -t --target-workspace --untracked"
    ;;
  diff)
    cmdOpts="-h --help -t --target-workspace"
    ;;
  init)
    cmdOpts="-h --help -c --catkin --cmake-prefix-path -t --target-workspace"
    ;;
  install)
    cmdOpts="-h --help -c --catkin --cmake-prefix-path -t --target-workspace --continue-on-error --delete-changed-uris --abort-changed-uris --backup-changed-uris --nocheckout --noupdates -y --confirm-all -m --merge-replace -k --merge-keep --merge-kill-append"
    ;;
  modify)
    cmdOpts="-h --help -t --target-workspace --git --svn --bzr --hg --uri --version-new --dettach -y --confirm"
    ;;
  remove)
    cmdOpts="-h --help -t --target-workspace"
    ;;
  snapshot)
    cmdOpts="-h --help -t --target-workspace"
    ;;
  info)
    cmdOpts="-h --help -t --target-workspace --data-only --no-pkg-path --pkg-path-only --localnames-only"
    ;;
  help|h|\?)
    cmdOpts="$cmds $qOpts"
    ;;
  *)
    ;;
  esac

  cmdOpts="$cmdOpts --help -h"

  # take out options already given
  for (( i=2; i<=$COMP_CWORD-1; ++i )) ; do
    opt=${COMP_WORDS[$i]}

    case $opt in
    --*)    optBase=${opt/=*/} ;;
    -*)     optBase=${opt:0:2} ;;
    esac

    cmdOpts=" $cmdOpts "
    cmdOpts=${cmdOpts/ ${optBase} / }

    # take out alternatives
    case $optBase in
    -h)                 cmdOpts=${cmdOpts/ --help / } ;;
    --help)             cmdOpts=${cmdOpts/ -h / } ;;
    -t)                 cmdOpts=${cmdOpts/ --target-workspace / } ;;
    --target-workspace) cmdOpts=${cmdOpts/ -t / } ;;
    -c)                 cmdOpts=${cmdOpts/ --catkin / } ;;
    --catkin)           cmdOpts=${cmdOpts/ -c / } ;;
    -n)                 cmdOpts=${cmdOpts/ --nobuild / } ;;
    --nobuild)          cmdOpts=${cmdOpts/ -n / } ;;
    esac

    # skip next option if this one requires a parameter
    if [[ $opt == @($optsParam) ]] ; then
      ((++i))
    fi
  done

  COMPREPLY=( $( compgen -W "$cmdOpts" -- $cur ) )

  return 0

}
complete -F _rosws_complete -o default rosws


