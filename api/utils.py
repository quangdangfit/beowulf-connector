import string

import random

from beowulf_connector.beowulf import commit


def randomString(stringLength=5):
    """Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(stringLength))


def generateAccountName(stringLength=5, worker_id=None):
    account_name = 'user0{}'.format(randomString(stringLength)) if worker_id else 'worker0{}'.format(
        randomString(stringLength))
    while commit.beowulfd.get_account(account_name):
        account_name = 'user0{}'.format(randomString(stringLength)) if worker_id else 'worker0{}'.format(
            randomString(stringLength))

    return account_name
