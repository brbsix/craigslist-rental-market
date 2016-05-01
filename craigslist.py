# -*- coding: utf-8 -*-

"""Display Craigslist rental market statistics"""

# standard imports
import argparse
import os
import re
import statistics
import time
from datetime import timedelta
from multiprocessing import Pool, cpu_count
from textwrap import dedent

# external imports
import appdirs
import inquirer
import requests
import requests_cache
from bs4 import BeautifulSoup


# pylint: disable=too-few-public-methods, too-many-instance-attributes
class Craigslist:

    """Scrape Craigslist listings and display resulting statistics"""

    def __init__(self):
        # default values
        self.minprice = 100
        self.maxprice = 30000
        self.url = 'https://sfbay.craigslist.org'

        # query values
        self.site = None
        self.region = None
        self.neighborhood = None
        self.bedrooms = None
        self.search = 'apa'

        # result values
        self.duration = 0
        self.prices = []

    def _getneighborhoods(self):
        """Return dictionary of neighborhoods for given site and region."""

        url = join(self.site, 'search', self.region, self.search)

        soup = getsoup(url)

        return {tag.next.strip(): tag.get('value') for tag
                in soup.select('input[name=nh]')}

    def _getprices(self):
        """Return list of prices for rental units."""
        base = join(self.site, 'search', self.region, self.search)

        # pylint: disable=protected-access
        encode_params = requests.models.RequestEncodingMixin._encode_params
        params = encode_params({
            'bedrooms': self.bedrooms,
            'max_price': self.maxprice,
            'min_price': self.minprice,
            'nh': self.neighborhood
        })

        urlpattern = '{}?s=%d&{}'.format(base, params)

        # create an iterator of all the URLs to query
        urls = (urlpattern % i for i in range(0, 2500, 100))

        # query pattern for prices of all n br rentals
        pattern = r'(?<=<span class="price">\$)([0-9]*?)' \
                  r'(?=</span> <span class="housing">/ %dbr )' % self.bedrooms

        # query HTML for all 2500 rental market listings
        html = concurrentdownload(urls)

        # extract prices
        strings = re.findall(pattern, html)

        # convert list of strings into integers
        prices = [int(i) for i in strings]

        return prices

    def _getregions(self):
        """Return default and dictionary of regions for given site."""

        url = join(self.site, 'search', self.search)
        soup = getsoup(url)
        tags = soup.select('#subArea > option')

        try:
            default = tags[0].text
            regions = {tag.text: tag.get('value') for tag in tags[1:]}
            return default, regions
        except IndexError:
            return None, {}

    def _getsites(self):
        """Return dictionary of major US city sites."""
        soup = getsoup(self.url)

        return {tag.text.replace('\xa0', ' '): tag.get('href') for tag in
                soup.find(text='us cities').next.select('li > a')[:-1]}

    def _print(self):
        """Print statistics and other informational text."""
        mean = statistics.mean(self.prices)
        median = statistics.median(self.prices)
        stdev = statistics.stdev(self.prices)
        high = mean + stdev
        low = mean - stdev

        print(dedent('''\
        Sourced %d prices in %.3f seconds

        Mean:\t$%.2f
        Median:\t$%.2f
        Hi/Lo:\t$%.2f/$%.2f
        StDev:\t%.2f
        ''' % (len(self.prices), self.duration,
               mean, median, high, low, stdev)))

    def _query(self):
        """Query user for information."""
        sites = self._getsites()

        results_site = inquirer.prompt([
            inquirer.List(
                'site',
                message='Which site?',
                choices=sorted(
                    sites,
                    key=lambda x: '!' if x == 'sf bayarea' else x
                )
            )
        ])['site']

        self.site = sites[results_site]

        # override NYC's funky apartment listings query
        if results_site == 'new york':
            self.search = 'aap'

        default_region, regions = self._getregions()

        if regions:
            results_region = inquirer.prompt([
                inquirer.List(
                    'region',
                    message='Which region?',
                    choices=[default_region] + sorted(
                        regions,
                        key=lambda x: x.lower()
                    )
                )
            ])['region']

            if results_region is not None:
                self.region = regions.get(results_region)

            if self.region is not None:
                neighborhoods = self._getneighborhoods()
                if neighborhoods:
                    results_neighborhood = inquirer.prompt([
                        inquirer.List(
                            'neighborhood',
                            message='Which neighborhood?',
                            choices=[None] + sorted(
                                neighborhoods,
                                key=lambda x: x.lower())
                        )
                    ])['neighborhood']

                    if results_neighborhood is not None:
                        self.neighborhood = neighborhoods[results_neighborhood]

        results_bedrooms = inquirer.prompt([
            inquirer.List('bedrooms',
                          message='How many bedrooms?',
                          choices=['%dbr' % i for i in range(1, 7)])
        ])['bedrooms']

        self.bedrooms = int(results_bedrooms.rstrip('br'))

    def run(self, cache=True):
        """Run application."""

        self._query()

        # configure `requests` cache
        if cache:
            cache_dir = appdirs.user_cache_dir('craigslist')
            os.makedirs(cache_dir, exist_ok=True)
            requests_cache.install_cache(
                cache_name=os.path.join(cache_dir, 'craigslist'),
                expire_after=timedelta(hours=0.5))

        print('Running query...\n')

        # record the start time
        start = time.time()

        self.prices = self._getprices()

        # determine elapsed time of queries
        self.duration = time.time() - start

        # remove expired cache entries
        if cache:
            requests_cache.core.remove_expired_responses()

        # print statistics (if any price data exists)
        if self.prices:
            self._print()
        else:
            print('Nothing found for that search.')


def _parser(args):
    """Parse command-line options."""

    # pylint: disable=too-few-public-methods
    class NegateAction(argparse.Action):
        """Support --toggle and --no-toggle options."""

        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, option_string[2:4] != 'no')

    parser = argparse.ArgumentParser(
        add_help=False,
        description='Display Craigslist rental market statistics.',
        usage='%(prog)s [OPTION]')
    parser.add_argument(
        '-h', '--help',
        action='help',
        help=argparse.SUPPRESS)
    parser.add_argument(
        '--cache', '--no-cache',
        action=NegateAction,
        default=True,
        help='cache network queries (default)',
        nargs=0)
    parser.add_argument(
        '--version',
        action='version',
        help=argparse.SUPPRESS,
        version='%(prog)s 0.0.4')

    return parser.parse_args(args).cache


def concurrentdownload(urls):
    """Download URLs concurrently and return their HTML."""
    processes = cpu_count() * 4
    with Pool(processes) as pool:
        return ''.join(pool.map(gethtml, urls))


def gethtml(url):
    """Return the HTML for a given URL."""
    return requests.get(url).text


def getsoup(url):
    """Return BeautifulSoup instance for given URL."""
    return BeautifulSoup(gethtml(url), 'html.parser')


def join(base, *components):
    """Join two or more URL components, inserting '/' as needed."""
    sep = '/'
    path = base
    for item in components:
        if item:
            if not path or path.endswith(sep):
                path += item
            else:
                path += sep + item
    return path


def main(args=None):
    """Start application."""
    cache = _parser(args)
    craigslist = Craigslist()
    craigslist.run(cache=cache)


if __name__ == '__main__':
    main()
