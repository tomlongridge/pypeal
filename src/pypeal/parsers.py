
from datetime import datetime
import re
from pypeal import config, utils
from pypeal.entities.method import Classification, Method, Stage
from pypeal.entities.peal import BellType, PealType
from pypeal.entities.peal_search import PealSearch

RINGER_NAME_REGEX = \
    re.compile(r'^(?:(?P<title>(?:' + '|'.join(utils.get_titles()) +
               r'))\.?\s+)?(?:(?P<given_names>.+?)\s+)??(?:(?P<last_name>[\S]+?))' +
               r'(?:\s\((?P<note>.+)\))?$',
               re.IGNORECASE)

METHOD_TITLE_NUMBER_OF_METHODS_REGEX = \
    re.compile(r'^(?P<num_methods>[0-9]+|' + '|'.join(utils.get_num_words()) + r')?\s?' +
               r'(?P<classification>' + '|'.join([s.value for s in Classification]) + r')?\s?' +
               r'(?P<stage>' + '|'.join([s.name for s in Stage]) + ')',
               re.IGNORECASE)

METHOD_TITLE_TWO_METHODS_REGEX = \
    re.compile(r'^(?:(?P<method_1>[\w\s\d]+?)\s)?' +
               r'(?:(?P<classification_1>' + '|'.join([s.value for s in Classification]) + r')\s)?' +
               r'(?:(?P<stage_1>' + '|'.join([s.name for s in Stage]) + r')\s)?' +
               r'and\s' +
               r'(?:(?P<method_2>[\w\s\d]+?)\s)?' +
               r'(?:(?P<classification_2>' + '|'.join([s.value for s in Classification]) + r')\s)?' +
               r'(?:(?P<stage_2>' + '|'.join([s.name for s in Stage]) + r'))?$',
               re.IGNORECASE)

# Match either a number and one of m, v or p as part of the title or, if in brackets, then allow just m, v or p with no number
# (e.g. (11m/v/p)) as this would be liable to match too much in normal text
METHOD_TITLE_NUM_METHODS_REGEX = re.compile(r'\(([0-9]*\s?[mvp]\/?)+\)|(([0-9]+\s?[mvp]\/?)+)|\(([0-9]*\smethods\/?)+\)')
METHOD_TITLE_NUM_METHODS_GROUP_REGEX = re.compile(r'([0-9]+[mvp])\/?')

CHANGES_PREFIX_REGEX = re.compile(r'^(?P<changes>[0-9]+)\s+(?:changes\s|each\s)?(?:of\s)?(?P<method>.*)$', re.IGNORECASE)

DURATION_REGEX = re.compile(r'^(?:(?P<hours>[0-9]{1,2})\s?(?:hours|hrs|hr|h))?\s?(?P<mins>[0-9]{1,4})?\s?(?:minutes|mins|min|m)?$')
TENOR_INFO_REGEX = re.compile(r'(?P<tenor_weight>[^in]+|size\s[0-9]+)(?:\sin\s(?P<tenor_note>.*))?$')

FOOTNOTE_RINGER_SEPARATORS = [' ', ',', '&', 'and']
FOOTNOTE_RINGER_LIST_PATTERN = r'(?P<bells>(?:(?:(?:[1-9][0-9]?(?:st|nd|rd|th)?)|' + \
                               r'(?:treble|tenor|' + '|'.join(utils.get_num_words()) + r'))\s?' + \
                               r'(?:' + '|'.join(FOOTNOTE_RINGER_SEPARATORS) + r')?\s?)+)'
FOOTNOTE_RINGER_REGEX_PREFIX = re.compile(r'^\(?' + FOOTNOTE_RINGER_LIST_PATTERN +
                                          r'\s?[-:\)]\s?(?P<footnote>.*)\.?$', re.IGNORECASE)
FOOTNOTE_RINGER_REGEX_SUFFIX = re.compile(r'^(?P<footnote>.*?)\s?(?:[-:\(]|for)?\s?' + FOOTNOTE_RINGER_LIST_PATTERN +
                                          r'\)?\.?$', re.IGNORECASE)
FOOTNOTE_CONDUCTOR_REGEX = re.compile(r'.*as cond(?:uctor)?.*', re.IGNORECASE)
FOOTNOTE_COMPOSER_REGEX = re.compile(r'.*(composed|composition) by\s(?P<composer>.*)$', re.IGNORECASE)
FOOTNOTE_ALL_BAND_REGEX = \
    re.compile(r'.*(?:for|by) (?:all|the whole)(?:(?: the)? band)?(?: (?:except for|except|apart from)(?: the)? (?P<exceptions>[^\.]+))?',
               re.IGNORECASE)
FOOTNOTE_JOINT_CONDUCTORS_REGEX = re.compile(r'Joint(?:ly)? conducted\s?(?:by)?\s?(?:(?:all )?the band)?' +
                                             FOOTNOTE_RINGER_LIST_PATTERN + r'?')


def _referenced_bells_to_list(bells_description: str, num_bells: int):
    bells = []
    for bell in re.split('|'.join(FOOTNOTE_RINGER_SEPARATORS), bells_description):
        if len(bell) == 0:
            continue
        elif bell[0].isnumeric():
            bell = bell.replace('st', '').replace('nd', '').replace('rd', '').replace('th', '')
            bells.append(int(bell))
        elif utils.word_to_num(bell) is not None:
            bells.append(utils.word_to_num(bell))
        elif bell.lower() == 'treble':
            bells.append(1)
        elif bell.lower() == 'tenor':
            bells.append(num_bells)
    if config.get_config('general', 'footnote_shift'):
        bells = [bell + config.get_config('general', 'footnote_shift') for bell in bells]
    return bells


def parse_method_title(title: str) -> tuple[list[Method], PealType, int, int, int]:

    methods: list[Method] = [Method()]
    methods[0].name = title
    peal_type: PealType = None
    num_methods: int = None
    num_variants: int = None
    num_principles: int = None

    # Catch titles with the number before the spliced/mixed definition
    # e.g. "Six Spliced Major"
    for title_word in methods[0].name.split(' ', 1):
        if title_word.lower().startswith('mixed'):
            peal_type = PealType.MIXED_METHODS
            methods[0].name = re.sub(r'[Mm]ixed ', '', methods[0].name)
        if title_word.lower().startswith('spliced'):
            peal_type = PealType.SPLICED_METHODS
            methods[0].name = re.sub(r'[Ss]pliced ', '', methods[0].name)

    # Catch titles such as "12 Doubles"
    if match := re.match(METHOD_TITLE_NUMBER_OF_METHODS_REGEX, methods[0].name):
        match_details = match.groupdict()
        if match_details['num_methods']:
            methods[0].name = methods[0].name[len(match_details['num_methods']) + 1:].strip()
            if match_details['num_methods'].isnumeric():
                num_methods = int(match_details['num_methods'])
            else:
                num_methods = utils.word_to_num(match_details['num_methods'])
        if match_details['classification']:
            methods[0].classification = Classification(match_details['classification'])
        methods[0].stage = Stage.from_method(match_details['stage'])
        methods[0].name = re.sub(METHOD_TITLE_NUMBER_OF_METHODS_REGEX, '', methods[0].name).strip()

        # Parse m/v/p detail in brackets
        if re.search(METHOD_TITLE_NUM_METHODS_REGEX, methods[0].name):
            multi_method_text = methods[0].name.strip('()')
            multi_method_match = re.findall(METHOD_TITLE_NUM_METHODS_GROUP_REGEX, multi_method_text)
            if len(multi_method_match) > 0:
                num_methods = num_variants = num_principles = 0
                for multi_method in multi_method_match:
                    match multi_method[-1]:
                        case 'm':
                            num_methods = int(multi_method.removesuffix('m'))
                        case 'v':
                            num_variants = int(multi_method.removesuffix('v'))
                        case 'p':
                            num_principles = int(multi_method.removesuffix('p'))
            elif multi_method_text.lower().endswith('methods'):
                multi_method_text = multi_method_text.lower().strip('methods').strip()
                if multi_method_text.isnumeric():
                    num_methods = int(multi_method_text)
            methods[0].name = re.sub(METHOD_TITLE_NUM_METHODS_REGEX, '', methods[0].name).strip()
            stage, classification, methods[0].name, _ = parse_single_method(methods[0].name, expect_changes=False)
            methods[0].stage = methods[0].stage or stage
            methods[0].classification = methods[0].classification or classification

        if methods[0].stage.value <= Stage.DOUBLES.value:
            peal_type = peal_type or PealType.MIXED_METHODS
        else:
            peal_type = peal_type or PealType.SPLICED_METHODS

    # Two named methods as the title
    elif match_details := re.search(METHOD_TITLE_TWO_METHODS_REGEX, methods[0].name):
        peal_type = peal_type or PealType.SPLICED_METHODS
        num_methods = 2
        match_details = match_details.groupdict()
        methods[0].name = match_details['method_1']
        methods[0].classification = Classification(match_details['classification_1']) if match_details['classification_1'] else None
        methods[0].stage = Stage.from_method(match_details['stage_1']) if match_details['stage_1'] else None
        methods.append(Method())
        methods[1].name = match_details['method_2']
        methods[1].classification = Classification(match_details['classification_2']) if match_details['classification_2'] else None
        methods[1].stage = Stage.from_method(match_details['stage_2']) if match_details['stage_2'] else None
        # If no method name given for second method, assume the same as the first
        # e.g. "Grandsire Caters and Royal"
        methods[1].name = methods[1].name or methods[0].name
        # If no stage or classification given for the first method, assume the same as the second
        # e.g. "Cambridge and Yorkshire Surprise Major"
        methods[0].classification = methods[0].classification or methods[1].classification
        methods[0].stage = methods[0].stage or methods[1].stage

        if max(methods[0].stage.value, methods[1].stage.value) <= Stage.DOUBLES.value:
            peal_type = peal_type or PealType.MIXED_METHODS
        else:
            peal_type = peal_type or PealType.SPLICED_METHODS
    else:
        methods[0].stage, methods[0].classification, methods[0].name, _ = parse_single_method(methods[0].name, expect_changes=False)
        if methods[0].stage is not None or methods[0].classification is not None:
            peal_type = PealType.SINGLE_METHOD
        else:
            # We've only matched a name (no stage or classification, so it's most likely general ringing)
            peal_type = PealType.GENERAL_RINGING

    for method in methods:
        if method.name is None:
            continue
        # Only trim Little and Differential methods as they appear in the title
        if method.name.lower().endswith('plain'):
            method.is_plain = True
        elif method.name.lower().endswith('little'):
            method.is_little = True
            method.name = method.name[:-6]
        elif method.name.lower().endswith('differential'):
            method.is_differential = True
            method.name = method.name[:-12]
        elif method.name.lower().endswith('treble dodging'):
            method.is_treble_dodging = True
        method.name = method.name if len(method.name) > 0 else None

    return (methods, peal_type, num_methods, num_variants, num_principles)


def parse_single_method(method: str, expect_changes: bool = True) -> tuple[Stage, Classification, str, int]:

    stage: Stage = None
    classification: Classification = None
    changes: int = None

    method = method.strip(' .,')

    if expect_changes and (match := re.match(CHANGES_PREFIX_REGEX, method)):
        changes = int(match.groupdict()['changes'])
        method = match.groupdict()['method'].strip(' .,')

    if (stage := Stage.from_method(method)):
        stage = stage
        method = method[:-len(stage.name)].strip(' .,')

    if method.lower().endswith("treble bob"):
        classification = Classification("Treble Bob")
    elif method.lower().endswith("treble place"):
        classification = Classification("Treble Place")
    elif method.lower().endswith("bob"):
        classification = Classification("Bob")
    elif method.lower().endswith("place"):
        classification = Classification("Place")
    elif method.lower().endswith("surprise"):
        classification = Classification("Surprise")
    elif method.lower().endswith("delight"):
        classification = Classification("Delight")
    elif method.lower().endswith("alliance"):
        classification = Classification("Alliance")
    elif method.lower().endswith("hybrid"):
        classification = Classification("Hybrid")
    if classification:
        method = method[:-len(classification.value)].strip(' .,')

    return (stage, classification, method, changes)


def parse_tenor_info(tenor_info_str: str) -> tuple[int, str]:
    if not (match := re.match(TENOR_INFO_REGEX, tenor_info_str)):
        raise ValueError(f'Unable to parse tenor info: {tenor_info_str}')
    tenor_weight: int = None
    tenor_note: str = None
    tenor_info = match.groupdict()
    if tenor_info['tenor_weight']:
        tenor_weight = parse_bell_weight(tenor_info['tenor_weight'])
    if tenor_info['tenor_note']:
        tenor_note = utils.convert_musical_key(tenor_info['tenor_note'].strip())
    return (tenor_weight, tenor_note)


def parse_bell_weight(weight_str: str) -> int:
    if weight_str is None:
        return None
    weight_lbs = None
    weight_str = weight_str.replace('–', '-').strip()
    if weight_str.endswith('cwt'):
        weight_lbs = int(weight_str[:-3]) * 112
    elif re.match(r'^[0-9]+(\-[0-9]+\-[0-9]+)?$', weight_str):
        weight_parts = weight_str.split('-')
        weight_lbs = int(weight_parts[0]) * 112
        if len(weight_parts) > 1:
            weight_lbs += int(int(weight_parts[1]) * (112/4))
            weight_lbs += int(weight_parts[2])
    else:
        raise ValueError(f'Unable to parse weight: {weight_str}')
    return weight_lbs


def parse_duration(duration_str: str) -> int:
    if not (duration_match := re.search(DURATION_REGEX, duration_str.strip())):
        raise ValueError(f'Unable to parse duration: {duration_str}')
    duration_info = duration_match.groupdict()
    duration = int(duration_info['hours'] or 0) * 60
    duration += int(duration_info['mins'] or 0)
    return duration


def parse_footnote(footnote: str, num_bells: int, conductor_bells: list[int]) -> tuple[list[int], list[int], str]:
    bells = []
    not_bells = []
    text = footnote.strip(' .')
    if re.match(r'.*cond(?:^\w|$).*', text):
        text = text.replace('cond', 'conductor')
    elif text.lower().endswith('as c'):
        text = text[:-4] + 'as conductor'
    elif text.lower().endswith('as (c)'):
        text = text[:-6] + 'as conductor'
    if len(text) == 0:
        text = None
    elif footnote_match := re.match(FOOTNOTE_JOINT_CONDUCTORS_REGEX, text):
        footnote_info = footnote_match.groupdict()
        if footnote_info['bells']:
            text = 'Jointly conducted.'
            conductor_bells = _referenced_bells_to_list(footnote_info['bells'], num_bells)
        else:
            text = 'Jointly conducted by all the band.'
            conductor_bells = list(range(1, num_bells + 1))
        bells = conductor_bells
    elif all_band_match := re.match(FOOTNOTE_ALL_BAND_REGEX, text):
        bells += list(range(1, num_bells + 1))
        excluded_ringers = all_band_match.groupdict()['exceptions']
        text += '.' if text[-1] != '.' else ''
        if excluded_ringers is not None:
            if 'conductor' in excluded_ringers.lower():
                not_bells += conductor_bells
                excluded_ringers = excluded_ringers.replace('the conductor', '')
                excluded_ringers = excluded_ringers.replace('conductor', '')
            elif 'treble' in excluded_ringers.lower():
                not_bells += [1]
                excluded_ringers = excluded_ringers.replace('the treble', '')
                excluded_ringers = excluded_ringers.replace('treble', '')
            elif 'tenor' in excluded_ringers.lower():
                not_bells += [num_bells]
                excluded_ringers = excluded_ringers.replace('the tenor', '')
                excluded_ringers = excluded_ringers.replace('tenor', '')
            for bell in re.split('|'.join(FOOTNOTE_RINGER_SEPARATORS), excluded_ringers):
                bell = bell.strip(' .,()')
                if len(bell) > 0 and bell.isnumeric():
                    not_bells += [int(bell)]
    else:
        if (footnote_match := re.match(FOOTNOTE_RINGER_REGEX_SUFFIX, text)) or \
                (footnote_match := re.match(FOOTNOTE_RINGER_REGEX_PREFIX, text)):
            footnote_info = footnote_match.groupdict()
            text = footnote_info['footnote'].strip().strip(':,')
            bells = _referenced_bells_to_list(footnote_info['bells'], num_bells)
        text += '.'
        if re.match(FOOTNOTE_CONDUCTOR_REGEX, text):
            bells += conductor_bells
    bells = [bell for bell in bells if bell not in not_bells]
    bells = list(dict.fromkeys(bells))  # de-dup
    return (sorted(bells) if len(bells) > 0 else None, conductor_bells, text)


def parse_footnote_for_composer(footnote: str) -> str:
    if composer_match := re.match(FOOTNOTE_COMPOSER_REGEX, footnote):
        return composer_match.groupdict()['composer']


def parse_ringer_name(full_name: str) -> tuple[str, str, str, str]:

    if not full_name:
        return (None, None, None, None)

    full_name = full_name.replace('.', '')
    if full_name[0] == '(' and full_name[-1] == ')':
        full_name = full_name[1:-1]

    if not (match := re.match(RINGER_NAME_REGEX, full_name.strip())):
        raise ValueError(f'Unable to parse ringer name: {full_name}')

    name_parts = match.groupdict()
    return (name_parts['last_name'], name_parts['given_names'], name_parts['title'], name_parts['note'])


def parse_bell_nums(bell_nums_str: str, max_bell_num: int = None) -> list[int]:
    bell_nums = []
    for bell in bell_nums_str.split(','):
        bell_list = bell.strip().split('-')
        match len(bell_list):
            case 1:
                if bell.isnumeric():
                    bell_nums.append(int(bell))
            case 2:
                if bell_list[0].strip().isnumeric() and bell_list[1].strip().isnumeric():
                    bell_nums += list(range(int(bell_list[0]), int(bell_list[1]) + 1))
    for bell in bell_nums:
        if bell < 1 or (max_bell_num and bell > max_bell_num):
            raise ValueError(f'Unexpected bell number "{bell}" - it must be more than 1 and less than or equal to {max_bell_num}')
    if len(bell_nums) == 0:
        raise ValueError(f'Unable to parse bell numbers: {bell_nums_str}')
    return bell_nums


def parse_search_url(url: str) -> PealSearch:

    if not url.startswith(config.get_config('bellboard', 'url')) or 'search.php' not in url:
        raise ValueError(f'Invalid Bellboard search URL: {url}')

    search = PealSearch()
    for param in url.split('?')[1].split('&'):
        key, value = param.split('=')
        if key == 'ringer':
            search.ringer_name = value
        elif key == 'from':
            search.date_from = datetime.strptime(value, '%d/%m/%Y').date()
        elif key == 'to':
            search.date_to = datetime.strptime(value, '%d/%m/%Y').date()
        elif key == 'dove_tower':
            search.tower_id = int(value)
        elif key == 'place':
            search.place = value
        elif key == 'region':
            search.region = value
        elif key == 'address':
            search.address = value
        elif key == 'association':
            search.association = value
        elif key == 'title':
            search.title = value
        elif key == 'bells_type':
            match value:
                case 'tower':
                    search.bell_type = BellType.TOWER
                case 'hand':
                    search.bell_type = BellType.HANDBELLS
        elif key == 'order':
            if 'newest' in value:
                search.order_by_submission_date = True
            if 'reverse' in value:
                search.order_descending = False

    return search
