rosinstall Package
==================

.. contents:: Contents
   :depth: 2

:mod:`rosinstall` Package
-------------------------

The rosinstall package currently contains all modules of rosinstall and rosws.

The `*_cmd` modules provide general services to query or modify the model.
They should keep printing and command line assumptions to a minimum, 
optimally functions in here should be callable from any UI.

The `*_cli` modules implement actual command line interface tools, and thus 
provide command line argument parsing and pretty printing. Optimally 
functions in here do not contain any algorithmic code that can be useful 
for more than one UI.


