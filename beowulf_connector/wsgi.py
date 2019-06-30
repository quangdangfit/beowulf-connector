"""
WSGI config for beowulf_connector project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beowulf_connector.settings')

# Beowulf
# Master key and account of service
from beowulf.beowulfd import Beowulfd
from beowulf.commit import Commit

from beowulf_connector import settings


active = settings.ACTIVE_KEY

creator = settings.CREATOR_NAME
default_pwd = settings.CREATOR_DEFAULT_PWD

commit = Commit(beowulfd_instance=Beowulfd(), no_wallet_file=True)
wallet = commit.wallet

wallet.unlock(default_pwd)

for pub in wallet.getPublicKeys():
    if wallet.getAccountFromPublicKey(pub) is None:
        wallet.removePrivateKeyFromPublicKey(pub)

if not wallet.getOwnerKeyForAccount(creator):
    wallet.addPrivateKey(active)

application = get_wsgi_application()
