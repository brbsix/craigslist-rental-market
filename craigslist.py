#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Get housing rental market stats from SF Craigslist"""

# standard imports
import re
import statistics
import time
from textwrap import dedent
from urllib.request import urlopen

# external imports
from bs4 import BeautifulSoup
import inquirer


def gethtml(url):
    """Return the HTML for a given URL."""

    return urlopen(url).read().decode('latin1')


def getneighborhoods(site, region):
    """Return dictionary of neighborhoods for given site and region."""

    url = '%ssearch/%s/apa' % (site, region)

    # override NYC's funky apartment listings
    if 'newyork' in site:
        url = re.sub(r'/apa$', '/aap', url)

    soup = getsoup(url)

    return {tag.next.strip(): tag.get('value') for tag
            in soup.select('input[name=nh]')}


def getprices(site, region, neighborhood, bedrooms):
    """Return list of prices for rental units."""

    urlpattern = '{}search/{}{}?s=%d&bedrooms={}&min_price=800{}'.format(
        site, region + '/' if region is not None else '', 'aap' if 'newyork'
        in site else 'apa', bedrooms, '&nh={}'.format(neighborhood) if
        neighborhood is not None else '')

    # create an iterator of all the URLs to query
    urls = (urlpattern % i for i in range(0, 2500, 100))

    # query pattern for prices of all n br rentals
    pattern = r'(?<=<span class="price">\$)([0-9]*?)' \
              r'(?=</span> <span class="housing">/ %dbr )' % bedrooms

    # query HTML for all 2500 rental market listings
    html = ''.join(gethtml(url) for url in urls)

    # extract prices
    strings = re.findall(pattern, html)

    # convert list of strings into integers
    prices = [int(i) for i in strings]

    return prices


def getregions(site):
    """Return default and dictionary of regions for given site."""

    url = site + 'search/apa'

    # override NYC's funky apartment listings
    if 'newyork' in site:
        url = re.sub(r'/apa$', '/aap', url)

    soup = getsoup(url)

    tags = soup.select('#subArea > option')

    try:
        return tags[0].text, {tag.text: tag.get('value') for tag in tags[1:]}
    except IndexError:
        return None, {}


def getsites():
    """Return dictionary of major US city sites."""

    url = 'https://sfbay.craigslist.org'

    soup = getsoup(url)

    return {tag.text.replace('\xa0', ' '): tag.get('href') for tag in
            soup.find(text='us cities').next.select('li > a')[:-1]}


def getsoup(url):
    """Return BeautifulSoup instance for given URL."""
    return BeautifulSoup(gethtml(url))


def getstats(prices, duration):
    """Return statistics and other informational text."""
    mean = statistics.mean(prices)
    median = statistics.median(prices)
    stdev = statistics.stdev(prices)
    high = mean + stdev
    low = mean - stdev

    return dedent('''\
    Sourced %d prices in %.3f seconds

    Mean:\t$%.2f
    Median:\t$%.2f
    Hi/Lo:\t$%.2f/$%.2f
    StDev:\t%.2f
    ''' % (len(prices), duration, mean, median, high, low, stdev))


def inquiry():
    """Query user for information."""
    neighborhood = None
    region = None

    sites = getsites()

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

    site = sites[results_site]

    default_region, regions = getregions(site)

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
            region = regions.get(results_region)

        if region is not None:
            neighborhoods = getneighborhoods(site, region)
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
                    neighborhood = neighborhoods[results_neighborhood]

    results_bedrooms = inquirer.prompt([
        inquirer.List('bedrooms',
                      message='How many bedrooms?',
                      choices=['%dbr' % i for i in range(1, 7)])
    ])['bedrooms']

    bedrooms = int(results_bedrooms.rstrip('br'))

    return site, region, neighborhood, bedrooms


def main():
    """Start application and prompt user."""

    site, region, neighborhood, bedrooms = inquiry()

    print('Running query...\n')

    # record the start time
    start = time.time()

    prices = getprices(site, region, neighborhood, bedrooms)

    # determine elapsed time of queries
    duration = time.time() - start

    # print statistics
    print(getstats(prices, duration))


if __name__ == '__main__':
    main()
