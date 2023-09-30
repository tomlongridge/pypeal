import configparser
import os

_config = None


def set_config_file(path: str):
    global _config
    _config = configparser.ConfigParser(delimiters='=',
                                        comment_prefixes='#',
                                        inline_comment_prefixes='#')
    _config.read(path)


def get_config(section: str) -> dict:
    global _config
    if _config is None:
        if 'PYPEAL_CONFIG' in os.environ:
            set_config_file(os.environ['PYPEAL_CONFIG'])
        elif os.path.exists(os.path.join(os.getcwd(), 'config.ini')):
            set_config_file(os.path.join(os.getcwd(), 'config.ini'))
        else:
            raise FileNotFoundError('No config.ini found in current directory or referenced by PYPEAL_CONFIG environment variable')
    return dict(_config.items(section))
