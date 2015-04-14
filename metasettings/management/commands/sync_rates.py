from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from optparse import make_option
from metasettings.openexchangerates import sync_rates


class Command(BaseCommand):
    can_import_settings = True

    option_list = BaseCommand.option_list + (
        make_option('--app_id',
                    dest='app_id',
                    default=None,
                    help='The openexchangerates APP ID'),

        make_option('--date_start',
                    dest='date_start',
                    default=None,
                    help='The date start to import currency rates'),

        make_option('--date_end',
                    dest='date_end',
                    default=None,
                    help='The date end to import currency rates'),
    )

    def handle(self, *args, **options):
        app_id = options.get('app_id', getattr(settings, 'OPENEXCHANGERATES_APP_ID', None))

        if not app_id:
            raise CommandError('The openexchangerates APP ID is required')

        start = options.get('date_start')
        end = options.get('date_end')

        if start is None and end is None:
            return sync_rates(app_id)

        if start:
            start = datetime.strptime(options.get('date_start'), "%Y-%m-%d").date()
        else:
            start = date.today()

        if end:
            end = datetime.strptime(options.get('date_end'), "%Y-%m-%d").date()
        else:
            end = date.today()

        date_start = date(start.year, start.month, 1)
        date_end = date(end.year, end.month, 1)

        if date_start and date_end:
            current = date_start

            while date_end >= current:
                sync_rates(app_id, current)
                current = current + relativedelta(months=1)
