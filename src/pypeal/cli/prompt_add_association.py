from pypeal.entities.association import Association
from pypeal.cli.prompts import ask, confirm
from pypeal.cli.chooser import choose_option
from pypeal.entities.peal import Peal


def prompt_add_association(association_name: str, peal: Peal, quick_mode: bool):

    if not association_name and (quick_mode or confirm('No linked association')):
        return

    matched_association: Association = None
    if association_name:
        if matched_associations := Association.search(name=association_name, exact_match=True):
            if len(matched_associations) == 1:
                matched_association = matched_associations[0]
            if not quick_mode and \
                    (association_name is not None and
                        not confirm(f'Matched "{association_name}" to association: {matched_association} ' +
                                    f'(ID: {matched_association.id})')) or \
                    (association_name is None and
                        not confirm(f'Add association {matched_association} (ID: {matched_association.id})')):
                matched_association = None
        else:
            print(f'No associations match "{association_name}"')

    while matched_association is None:

        match choose_option(['Search alternatives', 'Add new association', 'Remove association'], default=1):
            case 1:
                matched_association = prompt_find_association(association_name)
            case 2:
                matched_association = Association(ask('Name', default=association_name, required=True))
            case 3:
                break

    if matched_association and matched_association.id is None:
        matched_association.commit()
    peal.association = matched_association


def prompt_find_association(search_string: str = None) -> Association:
    while True:
        print('Enter search criteria:')
        search_string = ask('Name', default=search_string, required=True)

        association_results = Association.search(name=search_string, exact_match=False)
        match len(association_results):
            case 0:
                pass
            case 1:
                if confirm(f'Matched "{association_results[0]}" (ID: {association_results[0].id})', default=True):
                    return association_results[0]
            case _:
                print(f'{len(association_results)} associations match "{search_string}"')
                return choose_option(association_results, title='Choose association', none_option='None')
        if not confirm('Association not found.', confirm_message='Try again?', default=True):
            return None
