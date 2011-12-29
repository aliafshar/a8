# -*- coding: utf-8 -*- 
# (c) 2005-2011 PIDA Authors
# vim: ft=python sw=2 ts=2 sts=2 tw=80


from setuptools import setup
from a8 import version


setup(
  name = 'a8',
  author = 'Ali Afshar',
  author_email = 'aafshar@gmail.com',
  description = 'The Abominade IDE',
  license = 'GPL',
  url = 'http://abominade.org',
  version = version.VERSION,
  install_requires = [
    'psutil',
    'logbook',
    'pygtkhelpers>=0.4.3',
    'argparse',
    'pyyaml',
  ],
  packages = [
    'a8',
  ],
  package_data = {
    'a8': [
      'data/icons/*.png',
      'data/a8.vim',
    ],
  },
  entry_points = {
    'console_scripts': [
      'a8 = a8.__main__:main'
    ],
  },
  zip_safe = False,
)
