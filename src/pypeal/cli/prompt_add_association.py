from pypeal.entities.association import Association
from pypeal.cli.prompts import ask, confirm
from pypeal.cli.chooser import choose_option
from pypeal.entities.peal import Peal


def prompt_add_association(association: str, peal: Peal, quick_mode: bool):

    if not association and (quick_mode or confirm('No linked association')):
        return

    original_association_name = association
    matched_association: Association = None
    exact_match: bool = True
    while True:

        if association is not None:
            association_results = Association.search(name=association,
                                                     exact_match=exact_match)
        else:
            association_results = []

        match len(association_results):
            case 0:
                if association:
                    print(f'No associations match "{association}"')
                quick_mode = False
                match choose_option(['Search alternatives', 'Add new association', 'Remove association'], default=1):
                    case 1:
                        print('Enter search criteria:')
                        association = ask('Name', default=original_association_name, required=False)
                        exact_match = False
                        continue
                    case 2:
                        peal.association = Association(ask('Name', default=original_association_name, required=True))
                        peal.association.commit()
                        return
                    case 3:
                        return
            case 1:
                matched_association = association_results[0]
            case _:
                print(f'{len(association_results)} associations match "{association}"')
                quick_mode = False
                if not (matched_association := choose_option(association_results, none_option='None')):
                    association = None
                    continue

        if (quick_mode or
            (original_association_name is not None and
                confirm(f'Matched "{original_association_name}" to association: {matched_association} (ID: {matched_association.id})')) or
            (original_association_name is None and
                confirm(f'Add association {matched_association} (ID: {matched_association.id})'))):
            peal.association = matched_association
            return
        else:
            association = None
