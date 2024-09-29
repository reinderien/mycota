"""
Light MediaWiki API interface to fetch some template content
See https://en.wikipedia.org/wiki/Template:Mycomorphbox for the template definition
See
https://en.wikipedia.org/wiki/Special:WhatLinksHere?target=Template%3AMycomorphbox&namespace=0&hidetrans=0&hidelinks=1&hideredirs=1
for the list of transcluded articles
"""

import itertools
import logging
import pprint
import typing
from xml.etree import ElementTree

import requests

logger = logging.getLogger('api')

ARTICLE_NAMESPACE = 0


def query_mediawiki(
    session: requests.Session, warn: bool, log: bool, subquery: dict[str, typing.Any],
) -> typing.Iterator[dict[str, typing.Any]]:
    query = {
        # https://www.mediawiki.org/wiki/API:JSON_version_2
        'format': 'json',
        'formatversion': 2,
        # https://www.mediawiki.org/wiki/API:Query
        'action': 'query',
    } | subquery
    # https://www.mediawiki.org/wiki/Special:MyLanguage/API:Continue
    prev_continue = {}

    for chunk in itertools.count(1):
        with session.get(
            url='https://en.wikipedia.org/w/api.php', params=query | prev_continue,
        ) as resp:
            resp.raise_for_status()
            doc = resp.json()

        if warn:
            warnings = doc.get('warnings')
            if warnings:
                logger.warning(pprint.pformat(warnings))

        pages = doc['query']['pages']
        if log:
            logger.info('%s: %d chunks', subquery['prop'], chunk)
        yield from pages

        if doc.get('batchcomplete'):
            return
        prev_continue = doc.get('continue')


def get_transclusions(
    session: requests.Session,
    template: str,
    chunk_size: int = 500,  # max
) -> typing.Iterator[dict[str, typing.Any]]:
    """
    Stream out dictionaries of thin page references that have used (transcluded) the given
    template. Will work every chunk_size rows to fetch more records.
    """

    query = {
        # https://www.mediawiki.org/wiki/API:Query
        'titles': 'Template:' + template,
        'prop': 'transcludedin',
        # https://www.mediawiki.org/w/api.php?action=help&modules=query%2Btranscludedin
        'tiprop': 'pageid',  # omit title; we'll get it later
        'tinamespace': ARTICLE_NAMESPACE,
        'tishow': '!redirect',
        'tilimit': chunk_size,
    }

    for page in query_mediawiki(session=session, warn=True, log=True, subquery=query):
        for transclusion in page['transcludedin']:
            yield transclusion['pageid']


def get_template(
    session: requests.Session,
    pages: typing.Iterable[dict[str, typing.Any]],
    chunk_size: int = 50,  # max
) -> typing.Iterator[dict[str, typing.Any]]:
    """
    Stream out dictionaries containing XML blobs parsed from the wiki content. This method uses a
    deprecated 'parsetree', but it's the only reasonable way to query parsed templates over multiple
    pages; all new APIs require individual API calls. This will work every chunk_size rows to fetch
    more records.
    """

    query = {
        # https://www.mediawiki.org/wiki/API:Revisions
        'prop': 'revisions',
        'rvprop': 'parsetree',
    }

    n_pages = 0

    for i, batch in enumerate(itertools.batched(pages, n=chunk_size), start=1):
        n_pages += len(batch)
        logger.info('%s: %d chunks, %d pages', query['prop'], i, n_pages)
        query['pageids'] = '|'.join(str(pageid) for pageid in batch)
        yield from query_mediawiki(session=session, warn=False, log=False, subquery=query)


def template_xml_to_dict(tree: dict[str, typing.Any], template_name: str) -> dict[str, str]:
    """
    Simple but inefficienct traversal of an XML parse tree from WikiMedia. Returns a property
    dictionary from the template with the given name.
    Yes, this has to load the entire article.
    """
    main, = tree['revisions']
    root = ElementTree.fromstring(
        # Useful because the doc is riddled with whitespace
        ElementTree.canonicalize(xml_data=main['parsetree'], strip_text=True),
    )
    # Can't use ./template/title[.="{template}"]/../part
    # because the case of the template is inconsistent.
    for template in root.iterfind('.//template'):
        if template.find('title').text.casefold() == template_name.casefold():
            return {
                part.find('name').text: part.find('value').text
                for part in template.iterfind('./part')
            }
    logger.error('Failed to traverse XML for %s', tree['title'])
    return {}


def fetch_all(template: str) -> typing.Iterator[dict[str, typing.Any]]:
    """
    Make a session for cookies, and send off as many API requests as needed to lazy-yield
    property dictionaries from every page transcluding the named template.
    There is no guaranteed structure of the prop dictionaries; make that Pandas' problem.
    """
    with requests.Session() as session:
        session.headers = {'Accept': 'application/json'}
        pages = get_transclusions(session=session, template=template)
        for tree in get_template(session=session, pages=pages):
            props = {
                'title': tree['title'],
                'pageid': tree['pageid'],
            }
            props.update(template_xml_to_dict(tree, template_name=template))
            yield props
