import hashlib
import os
from bs4 import BeautifulSoup
import sys
sys.path.append('src')
from pypeal.bellboard import download_peal, get_id_from_url, get_peal_from_html  # noqa: E402


with open(os.path.join(os.path.dirname(__file__), '..', 'files', 'ringer_test_names.txt'), 'r') as f:
    RINGER_NAMES = [r for r in f.read().split('\n')]


def generate_peal(url: str):

    url, html = download_peal(url)
    id = get_id_from_url(url)

    out_file_name = os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'pages', f'{id}.html')

    soup = BeautifulSoup(html, 'html.parser')

    print('\n##############################################\n')
    print(soup.select("div.performance")[0].text)
    print('##############################################\n')

    print('Stripping changing and personal information...')
    for metadata in [*soup.select('p.metadata'),
                     *soup.select('div#performance-ad'),
                     *soup.select('ul.control'),
                     *soup.select('script'),
                     *soup.select('td#page-footer')]:
        metadata.replace_with('')
    bell_num = 1
    for metadata in [*soup.select('span.ringer.persona')]:
        metadata.string.replace_with(anonymize_ringer(metadata.string))
        bell_num += 1

    print(f'Writing peal to {out_file_name}...')
    with open(out_file_name, 'w') as f:
        f.write(str(soup))

    print('Parsing peal...')
    bb_peal = get_peal_from_html(id, str(soup))

    out_file_name = os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'parsed', f'{id}.txt')
    print(f'Writing peal to {out_file_name}...')
    with open(out_file_name, 'w') as f:
        f.write(str(bb_peal))

    print('\n##############################################\n')
    print(str(bb_peal))
    print('\n##############################################\n')


def anonymize_ringer(name: str) -> str:
    index = int(hashlib.md5(name.encode('utf-8')).hexdigest(), 16) % len(RINGER_NAMES)
    return RINGER_NAMES[index]


if len(sys.argv) == 2:
    generate_peal(sys.argv[1])
else:
    for file in os.listdir(os.path.join(os.path.dirname(__file__), '..', 'files', 'peals', 'pages')):
        generate_peal('https://bb.ringingworld.co.uk/view.php?id=' + file.split('.')[0])
