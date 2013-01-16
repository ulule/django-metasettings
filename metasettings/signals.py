import django.dispatch

currency_was_set = django.dispatch.Signal(providing_args=['request', 'currency_code'])

language_was_set = django.dispatch.Signal(providing_args=['request', 'language_code'])
