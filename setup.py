#!/usr/bin/env python

from distutils.core import setup
from pathlib import Path


setup(
      name='logcheck',
      version='1.0',
      description='Python Slack Integration for AI check',
      long_description=Path('README.md').read_text(),
      author='Jan Rygl',
      author_email='jan.rygl@aicheck.tech',
      maintainer='Jan Rygl',
      maintainer_email='jan.rygl@aicheck.tech',
      url='https://github.com/aicheck-tech/logcheck',
      keywords='logging, logrotate, slack',
      packages=['logcheck'],
      py_modules=['logcheck'],
      install_requires=[item for item in Path('requirements.txt').read_text().split("\n") if item],
      )
