rosinstall Package
==================

.. contents:: Contents
   :depth: 2

:mod:`rosinstall` Package
-------------------------

The rosinstall package currently contains all modules of rosinstall and rosws.

there is a vision of splitting out all ROS dependent functionality into 
a separate tool, to leave a pure multi-vcs tool. This split is already half 
evident in the modules.

The architecture can be imagined to have 3 layers, on top of the 
vcstools library.

The lowest layer is the model layer, which is all the `config_*` modules.
The main model class is .. autosummary:: rosinstall.config.

The `*_cmd` modules provide general services to query or modify the model.
They should keep printing and command line assumptions to a minimum, 
optimally functions in here should be callable from any UI.

The `*_cli` modules implement actual command line interface tools, and thus 
provide command line argument parsing and pretty printing. Optimally 
functions in here do not contain any algorithmic code that can be useful 
for more than one UI.


The Model
=========

The model of rosinstall is that a config maintains a list of elements, 
and performs defines operations on the list. The config class is 
responsible for ensuring consistency, such as not having two elements 
with the same localname.

A config element defines one main function `install`, which eventually 
calls an SCM provider to checkout or update code.



ROS dependent modules
=====================

These modules provide functions on top of the multiproject context with reference to ROS.

:mod:`rosinstall_cli` Module
----------------------------

.. automodule:: rosinstall.rosinstall_cli
    :members:
    :special-members:
    :undoc-members:
    :show-inheritance:


:mod:`rosws_cli` Module
-----------------------

.. automodule:: rosinstall.rosws_cli
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`rosws_stacks_cli` Module
------------------------------

.. automodule:: rosinstall.rosws_stacks_cli
    :members:
    :special-members:
    :undoc-members:
    :show-inheritance:

:mod:`rosinstall_cmd` Module
----------------------------

.. automodule:: rosinstall.rosinstall_cmd
    :members:
    :undoc-members:
    :show-inheritance:


:mod:`helpers` Module
---------------------

.. automodule:: rosinstall.helpers
    :members:
    :undoc-members:
    :show-inheritance:


:mod:`setupfiles` Module
------------------------

.. automodule:: rosinstall.setupfiles
    :members:
    :undoc-members:
    :show-inheritance:

:mod:`locate` Module
--------------------

.. automodule:: rosinstall.locate
    :members:
    :undoc-members:
    :show-inheritance:



:mod:`simple_checkout` Module
-----------------------------

.. automodule:: rosinstall.simple_checkout
    :members:
    :undoc-members:
    :show-inheritance:


