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