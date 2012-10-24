def ros_found_in_yaml(yaml_elements):
    '''
    Checks whether given yaml contains an element we can identify as ros stack
    '''
    ros_found = False
    print(yaml_elements)
    for e in yaml_elements:
        scm_found = False
        for scm in ['svn', 'tar', 'git', 'hg']:
            if scm in e:
                scm_found = True
                element = e[scm]
                if "local-name" in element:
                    if element["local-name"] == "ros":
                        ros_found = True
                        break
        if not scm_found:
            element = e.get("other", '')
            if "local-name" in element:
                if element["local-name"].endswith('/ros'):
                    ros_found = True
    return ros_found


def ros_found_in_path_spec(specs):
    ros_found = False
    for s in specs:
        if "svn" == s.get_scmtype() or "tar" == s.get_scmtype() or s.get_scmtype() is None:
            if s.get_path().endswith('ros'):
                ros_found = True
                break
    return ros_found
