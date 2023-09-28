import configparser
import os

_config = None


def get_config(section: str) -> dict:
    global _config
    if _config is None:
        _config = configparser.ConfigParser(delimiters='=',
                                            comment_prefixes='#',
                                            inline_comment_prefixes='#')

        if 'PYPEAL_CONFIG' in os.environ:
            _config.read(os.environ['PYPEAL_CONFIG'])
        elif os.path.exists(os.path.join(os.getcwd(), 'config.ini')):
            _config.read(os.path.join(os.getcwd(), 'config.ini'))
        else:
            raise FileNotFoundError('No config.ini found in current directory or referenced by PYPEAL_CONFIG environment variable')
    return dict(_config.items(section))
