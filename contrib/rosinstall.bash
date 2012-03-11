# rosinstall bash completion support. Source this file to get the completion in bash.

_rosinstall_complete()
{
  local cur cmdOpts
  cur=${COMP_WORDS[COMP_CWORD]}

  if [[ "$cur" == -* ]] ; then
      cmdOpts="-h --help -n -c --catkin --cmake-prefix-path --continue-on-error --delete-changed-uris --abort-changed-uris --backup-changed-uris --version --nobuild --rosdep-yes --diff --status"
  fi

  # take out options already given
  for (( i=1; i<=$COMP_CWORD-1; ++i )) ; do
    opt=${COMP_WORDS[$i]}

    case $opt in
    --*)    optBase=${opt/=*/} ;;
    -*)     optBase=${opt:0:2} ;;
    esac

    cmdOpts=" $cmdOpts "
    cmdOpts=${cmdOpts/ ${optBase} / }

    # take out some alternatives
    case $optBase in
    -h)                 cmdOpts="" ;;
    --help)             cmdOpts="" ;;
    --version)          cmdOpts="" ;;
    --diff)             cmdOpts="" ;;
    --status)           cmdOpts="" ;;
    --status-untracked) cmdOpts="" ;;
    -c)                 
      cmdOpts=${cmdOpts/ --catkin / }
      cmdOpts=${cmdOpts/ --nobuild / }
      cmdOpts=${cmdOpts/ -n / }
      cmdOpts=${cmdOpts/ --rosdep-yes / }
    ;;
    --catkin)           
      cmdOpts=${cmdOpts/ -c / }
      cmdOpts=${cmdOpts/ --nobuild / }
      cmdOpts=${cmdOpts/ -n / }
      cmdOpts=${cmdOpts/ --rosdep-yes / }
    ;;
    -n)                 cmdOpts=${cmdOpts/ --nobuild / } ;;
    --nobuild)          cmdOpts=${cmdOpts/ -n / } ;;
    --delete-changed-uris) 
      cmdOpts=${cmdOpts/ --abort-changed-uris / }
      cmdOpts=${cmdOpts/ --backup-changed-uris / }
    ;;
    --abort-changed-uris)
      cmdOpts=${cmdOpts/ --delete-changed-uris / }
      cmdOpts=${cmdOpts/ --backup-changed-uris / }
    ;;
    --backup-changed-uris) 
      cmdOpts=${cmdOpts/ --delete-changed-uris / }
      cmdOpts=${cmdOpts/ --abort-changed-uris  / }
    ;;

    esac

    # skip next option if this one requires a parameter
    if [[ $opt == @($optsParam) ]] ; then
      ((++i))
    fi
  done

  COMPREPLY=( $( compgen -W "$cmdOpts" -- $cur ) )

  return 0

}

complete -F _rosinstall_complete -o default rosinstall