# -*- coding: utf-8 -*-

from setuptools import setup


def read(filename):
    with open(filename) as f:
        return f.read()


setup(
    name='craigslist-rental-market',
    version='0.0.5',
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
        'requests', 'requests-cache-latest'
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
