import hashlib
import os
import re
from bs4 import BeautifulSoup

import sys
from pypeal.bellboard.html_generator import METADATA_IMPORTED_REGEX, METADATA_SUBMITTED_REGEX
sys.path.append('src')
from pypeal.bellboard.interface import get_id_from_url, request  # noqa: E402

SEARCH_RESPONSE_PAGE_SIZE: int = 5

with open(os.path.join(os.path.dirname(__file__), '..', 'files', 'ringer_test_names.txt'), 'r') as f:
    RINGER_NAMES = [r for r in f.read().split('\n')]


def generate_peal(url: str):

    url, html = request(url)
    id = get_id_from_url(url)
    file_name = str(id).zfill(7) + '.html'
    file_path = os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'pages', file_name)

    soup = BeautifulSoup(html, 'html.parser')

    print('\n##############################################\n')
    print(soup.select("div.performance")[0].text)
    print('##############################################\n')

    print('Stripping changing and personal information...')
    for metadata in [*soup.select('div#performance-ad'),
                     *soup.select('ul.control'),
                     *soup.select('script'),
                     *soup.select('td#page-footer'),
                     *soup.select('div.like'),
                     *soup.select('link[rel="stylesheet"]')]:
        metadata.replace_with('')
    for metadata in [*soup.select('p.metadata')]:
        if metadata.text.startswith('This performance has been viewed'):
            metadata.replace_with('')

    for ringer in [*soup.select('span.ringer.persona')]:
        if len(ringer.string.strip(' -')):
            ringer.string.replace_with(anonymize_ringer(ringer.string))

    composer_element = soup.select('span.composer.persona')
    if len(composer_element) > 0:
        composer_element[0].string.replace_with(anonymize_ringer(composer_element[0].string))

    for metadata in [*soup.select('p.metadata')]:
        if match := re.match(METADATA_SUBMITTED_REGEX, metadata.text):
            submitter = match.groupdict()['submitter']
            if submitter is not None:
                metadata.contents[0].string.replace_with(metadata.text.replace(submitter, anonymize_ringer(submitter)))
        elif match := re.match(METADATA_IMPORTED_REGEX, metadata.text):
            submitter = match.groupdict()['submitter']
            if submitter is not None:
                metadata.contents[0].string.replace_with(metadata.text.replace(submitter, anonymize_ringer(submitter)))

    print(f'Writing peal to {file_path}...')
    with open(file_path, 'w') as f:
        f.write(str(soup))


def regenerate_all():
    for file in os.listdir(os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'pages')):
        generate_peal('https://bb.ringingworld.co.uk/view.php?id=' + file.split('.')[0])


def regenerate_search_response():
    page_count = 0
    page_size = 0
    file_ptr = None
    peal_files = os.listdir(os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'pages'))
    for peal_file in sorted(peal_files):
        if file_ptr is None or page_size > SEARCH_RESPONSE_PAGE_SIZE:
            if file_ptr is not None:
                file_ptr.write('</performances>')
                f.close()
            page_count += 1
            page_size = 0
            file_ptr = open(os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'searches', f'{page_count}.xml'), 'w')
            file_ptr.write('<performances xmlns="http://bb.ringingworld.co.uk/NS/performances#">\n')
        file_ptr.write(f'  <performance href="view.php?id={peal_file.split(".")[0]}"/>\n')
        page_size += 1
    file_ptr.write('</performances>')
    file_ptr.close()


def anonymize_ringer(name: str) -> str:
    index = int(hashlib.md5(name.encode('utf-8')).hexdigest(), 16) % len(RINGER_NAMES)
    return RINGER_NAMES[index]


if len(sys.argv) == 2:
    generate_peal(sys.argv[1])
else:
    regenerate_all()
regenerate_search_response()
