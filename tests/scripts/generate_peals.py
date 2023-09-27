import os
from bs4 import BeautifulSoup
from requests import Response, get as get_request
import sys
sys.path.append('.')
import pypeal.bellboard  # noqa: E402

INT_TO_WORD_MAP = {
    1: 'First', 2: 'Second', 3: 'Third', 4: 'Fourth', 5: 'Fifth',
    6: 'Sixth', 7: 'Seventh', 8: 'Eighth', 9: 'Ninth', 10: 'Tenth',
    11: 'Eleventh', 12: 'Twelfth', 13: 'Thirteenth', 14: 'Fourteenth',
    15: 'Fifteenth', 16: 'Sixteenth', 17: 'Seventeenth', 18: 'Eighteenth',
    19: 'Nineteenth', 20: 'Twentieth'
}


def generate_peal(url: str):

    print(f'Getting peal at {url}')
    response: Response = get_request(url)
    id = response.url.split('=')[1]
    print(f'Downloaded peal at {id}')

    out_file_name = f'tests/peals/pages/{id}.html'

    soup = BeautifulSoup(response.text, 'html.parser')

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
        anonymous_name = INT_TO_WORD_MAP[bell_num]
        for name in metadata.string.split(' ')[1:]:
            anonymous_name += ' Ringer'
        metadata.string.replace_with(anonymous_name)
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


if len(sys.argv) == 2:
    generate_peal(sys.argv[1])
else:
    for file in os.listdir('tests/peals/pages'):
        generate_peal(pypeal.bellboard.get_url_from_id(int(file.split('.')[0])))
