import json
import requests
import logging

from .models import CurrencyRate

LOGGER = logging.getLogger(__name__)


def rate_request(app_id, date=None):
    url = 'http://openexchangerates.org/api'
    if date:
        url += '/historical/%s.json' % date.strftime("%Y-%m-%d")
    else:
        url += '/latest.json'

    response = requests.get(url, params={'app_id': app_id})

    if response.status_code == 200:
        return json.loads(response.content)

    LOGGER.warning("Request to %s returned %s", url, response.status_code)


def sync_rates(app_id, date=None):
    result = rate_request(app_id, date=None)

    if not result:
        return

    for currency, rate in result['rates'].items():
        currency_rate, created = CurrencyRate.objects.update_or_create(
            currency, rate, date
        )
        if currency_rate:
            if created:
                msg = 'Create currency %s with %s'
            else:
                msg = 'Syncing currency %s with %s'

            LOGGER.info(msg, currency, rate)
