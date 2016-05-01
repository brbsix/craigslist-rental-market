# -*- coding: utf-8 -*-
"""
Application setup script

To build package:
python3 setup.py sdist bdist_wheel clean
"""

import os

from setuptools import setup


def read(path):
    """Convert Markdown to reStructuredText if possible."""
    with open(path) as file_object:
        text = file_object.read()

    try:
        import pypandoc
        return pypandoc.convert(text, 'rst', 'md')
    except ImportError:
        return text


# allow setup.py to be run from any path
os.chdir(os.path.dirname(os.path.abspath(__file__)))

setup(
    name='craigslist-rental-market',
    version='0.0.8',
    description='Display Craigslist rental market statistics',
    author='Brian Beffa',
    author_email='brbsix@gmail.com',
    long_description=read('README.md'),
    url='https://github.com/brbsix/craigslist-rental-market',
    license='GPLv3',
    keywords=['craigslist', 'scraper', 'scraping'],
    py_modules=['craigslist'],
    install_requires=[
        'appdirs', 'beautifulsoup4', 'inquirer',
        'requests', 'requests-cache>=0.4.11'
    ],
    entry_points={
        'console_scripts': ['craigslist=craigslist:main'],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.0',
        'Programming Language :: Python :: 3.1',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Utilities',
    ],
)
