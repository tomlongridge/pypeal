import hashlib
import os
from bs4 import BeautifulSoup
import sys
sys.path.append('.')
import pypeal.bellboard  # noqa: E402


with open('tests/data/ringer_test_names.txt', 'r') as f:
    RINGER_NAMES = [r for r in f.read().split('\n')]


def generate_peal(url: str):

    id, html = pypeal.bellboard.download_peal(url)

    out_file_name = f'tests/peals/pages/{id}.html'

    soup = BeautifulSoup(html, 'html.parser')

    print('\n##############################################\n')
    print(soup.select("div.performance")[0].text)
    print('##############################################\n')

    print('Stripping changing and personal information...')
    for metadata in [*soup.select('p.metadata'),
                     *soup.select('div#performance-ad'),
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
    bb_peal = pypeal.bellboard.get_peal(id, str(soup))

    out_file_name = f'tests/peals/parsed/{id}.txt'
    print(f'Writing peal to {out_file_name}...')
    with open(out_file_name, 'w') as f:
        f.write(str(bb_peal))

    print('\n##############################################\n')
    print(str(bb_peal))
    print('##############################################\n')


def anonymize_ringer(name: str) -> str:
    index = int(hashlib.md5(name.encode('utf-8')).hexdigest(), 16) % len(RINGER_NAMES)
    return RINGER_NAMES[index]


if len(sys.argv) == 2:
    generate_peal(sys.argv[1])
else:
    for file in os.listdir('tests/peals/pages'):
        generate_peal(pypeal.bellboard.get_url_from_id(int(file.split('.')[0])))
