import logging
from datetime import datetime, timedelta

import requests
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from api.models import Account, Transfer
from beowulf_connector import settings
from beowulf_connector.beowulf import commit


_logger = logging.getLogger('api')


class Command(BaseCommand):

    def handle(self, *args, **options):
        _logger.info("[CRON][pay_workers] Starting...")
        sid = transaction.savepoint()

        try:
            url = settings.GET_WORKER_DETAIL_URL
            if not url:
                raise Exception('Worker detail url not found!')

            response = requests.get(url)
            res_data = response.json()
            # res_data = {
            #     "workers": [
            #         {
            #             "id": "QmPM1djLr1RDYmnat5Ht5NembsogDe7YSmR87AeMgZ2VPB",
            #             "address": "192.168.1.4:5001",
            #             "total_storing": 10,
            #             "total_missing": 1,
            #             "total_down": 0,
            #             "is_busy": False
            #         },
            #         {
            #             "id": "QmPM1djLr1RDYmnat5Ht5NembsogDe7YSmR87AeMgZ2VPq",
            #             "address": "192.168.1.5:5001",
            #             "total_storing": 15,
            #             "total_missing": 1,
            #             "total_down": 0,
            #             "is_busy": False
            #         },
            #     ]
            # }

            workers = res_data.get('workers')

            for worker in workers:
                worker_id = worker.get('id')

                try:
                    worker_account = Account.objects.get(worker_id=worker_id)
                except Account.DoesNotExist:
                    raise Exception('Worker #{} does not exists!'.format(worker_id))

                receiver = worker_account.account_name
                sender = settings.CREATOR_NAME

                total_storing = worker.get('total_storing')
                amount = total_storing * settings.WORKER_PAY_AMOUNT
                memo = 'GFS pay for worker storing, total storing: {} GB, amount: {} BWF/GB, total: {} BWF' \
                    .format(total_storing, settings.WORKER_PAY_AMOUNT, amount)

                asset = 'BWF'
                fee = settings.TRANSFER_FEE
                asset_fee = settings.TRANSFER_ASSET_FEE

                Transfer.objects.create(sender=sender, receiver=receiver, amount=amount, memo=memo, asset=asset)

                commit.transfer(receiver, amount, asset, fee, asset_fee, memo, sender)
                _logger.info("[CRON][pay_workers] Paid worker #{}, amount: {}, amount".format(worker_id, amount))

            transaction.savepoint_commit(sid)

        except Exception as e:
            transaction.savepoint_rollback(sid)
            raise e
