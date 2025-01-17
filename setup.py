#!/usr/bin/env python

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('requirements.txt', 'r') as f:
    requirements = f.read().splitlines()


SUB_MODULES=[
        'enzy_htp',
        'enzy_htp._config',
        'enzy_htp._interface',
        'enzy_htp._interface.handle_types',
        'enzy_htp.core',
        'enzy_htp.core.clusters',
        'enzy_htp.chemical',
        'enzy_htp.structure',
        'enzy_htp.structure.structure_io',
        'enzy_htp.structure.structure_operation',
        'enzy_htp.structure.structure_enchantment',
        'enzy_htp.structure.structure_region',
        'enzy_htp.structure.structure_selection',
        'enzy_htp.structure.structure_selection_class',
        'enzy_htp.structure.structure_constraint',
        'enzy_htp.structure.structure_translator',
        'enzy_htp.quantum',
        'enzy_htp.electronic_structure',
        'enzy_htp.preparation',
        'enzy_htp.mutation',
        'enzy_htp.mutation.mutation_pattern',
        'enzy_htp.mutation_class',
        'enzy_htp.geometry',
        'enzy_htp.analysis',
]

if __name__ == '__main__':
    setup(
        name='enzy_htp',
        version='2.0.0',
        description='EnzyHTP automates the complete life-cycle of enzyme modeling',
        author='EnzyHTP Authors',
        author_email='zhongyue.yang@vanderbilt.edu',
        include_package_data=True,
        packages=SUB_MODULES,
        install_requires=requirements,
        )
