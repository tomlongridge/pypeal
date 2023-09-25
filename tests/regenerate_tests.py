import os
from bs4 import BeautifulSoup
from requests import Response, get as get_request
import sys
sys.path.append('src')
from pypeal.bellboard import BellboardSearcher  # noqa: E402

for file in os.listdir('tests/peals/pages'):

    id = int(file.split('.')[0])
    url = f'https://bb.ringingworld.co.uk/view.php?id={id}'

    print(f'Getting peal at {url}')
    response: Response = get_request(url)
    id = response.url.split('=')[1]
    print(f'Downloaded peal at {id}')

    out_file_name = f'tests/peals/pages/{id}.html'

    print('Stripping changing and personal information...')
    soup = BeautifulSoup(response.text, 'html.parser')
    for metadata in [*soup.select('p.metadata'),
                     *soup.select('div#performance-ad'),
                     *soup.select('td#page-footer')]:
        metadata.replace_with('')
    bell_num = 1
    for metadata in [*soup.select('span.ringer.persona')]:
        metadata.string.replace_with(f'Ringer {bell_num}')
        bell_num += 1

    print(f'Writing peal to {out_file_name}...')
    with open(out_file_name, 'w') as f:
        f.write(str(soup))

    print('Parsing peal...')
    bb_peal = BellboardSearcher().get_peal(id, str(soup))

    out_file_name = f'tests/peals/parsed/{id}.txt'
    print(f'Writing peal to {out_file_name}...')
    with open(out_file_name, 'w') as f:
        f.write(str(bb_peal))

    print('\n##############################################\n')
    print(str(bb_peal))
    print('##############################################\n')
