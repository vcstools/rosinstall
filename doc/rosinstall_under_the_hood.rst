rosinstall under the hood
=========================

This is a summary of how rosinstall works under the hood.  

Process Flow
------------

Whenever rosinstall is executed the following code path is followed:

#. Gather command line arguments
#. Merge source rosinstall files
#. Install source
#. Generate a setup file. 

Merging source rosinstall files
-------------------------------

1. Rosinstall will start with the `.rosinstall` file in the install path.  
 * If one doesn't exist it will create an empty one.  
2. To this it will append the contents of all arguments in order left to right.  
  * if the argument is a directory it will look for a `DIRECTORY/.rosinstall` and add all elements as `other` elements with `local-name` set to the full path.
  * if the argument is a url or a path to a file it will directly take the contents
3. Duplicates will be removed based on the key 'local-name'.  The later definition will be preserved.  
4. This `.rosinstall` file will be saved to disk.

Installing Source
-----------------

#. rosinstall will iterate through the `.rosinstall` file for each definition of source. 
#. If the source directory does not exist it will be created and checked out
#. if the source directory exists and is of the same `uri` it will be updated
#. If the source directory exists and the uri doesn't match the user will be prompted to abort, delete, or backup 


Generating setup.bash
---------------------

1. After a successful installation `rosinstall` will iterate through each of the elements in `.rosinstall` and add their `local-name` to the ROS_PACKAGE_PATH, unless the path is detected to be ros, in which case it will be set to ROS_ROOT.  
 * This will error if a ROS directory is not detected.  (The ros directory must be explicitly called out in the `local-name`)
2. The setup file will be written to disk.
