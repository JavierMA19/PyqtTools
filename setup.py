#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 23 10:30:42 2019

@author: jmartinez
"""

from setuptools import setup, find_packages

_version = '0.0.3'

long_description = """
                   Tools for acquire continuously                 
                   """

install_requires = [
                    'numpy',
                    'PyDAQmx',
                    'matplotlib',
                    'quantities>=0.12',
                    'scipy',
                    'neo==0.6.1',
                    ]

console_scripts = [
                  ]

entry_points = {'console_scripts': console_scripts, }

classifiers = ['Development Status :: 3 - Alpha',
               'Environment :: Console',
               'Environment :: X11 Applications :: Qt',
               'Environment :: Win32 (MS Windows)',
               'Intended Audience :: Science/Research',
               'License :: OSI Approved :: GNU General Public License (GPL)',
               'Operating System :: Microsoft :: Windows',
               'Operating System :: POSIX',
               'Operating System :: POSIX :: Linux',
               'Operating System :: Unix',
               'Operating System :: OS Independent',
               'Programming Language :: Python',
               'Programming Language :: Python :: 2.7',
               'Topic :: Scientific/Engineering',
               'Topic :: Software Development :: User Interfaces']

setup(name="PyqtTools",
      version=_version,
      description="Time continuous acquisition tools",
      long_description=long_description,
      author="Javier Martínez-Aguilar",
      author_email="Javier.Martinez@imb-cnm.csic.es",
      maintainer="Javier Martinez-Aguilar",
      maintainer_email="Javier.Martinez@imb-cnm.csic.es",
      url="https://github.com/jmartinezaguilar/PyCont",
      download_url="https://github.com/jmartinezaguilar/PyCont",
      license="GPLv3",
      packages=find_packages(),
      classifiers=classifiers,
      entry_points=entry_points,
      install_requires=install_requires,
      include_package_data=True,
      )
