from .choices import CURRENCY_CHOICES, CURRENCY_LABELS


def base(request):
    return {
        'CURRENCY_CHOICES': CURRENCY_CHOICES,
        'CURRENCY_LABELS': CURRENCY_LABELS
    }
