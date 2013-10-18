import re

from django import template

from metasettings.models import (get_currency_from_request as get_currency,
                                 get_language_from_request as get_language,
                                 convert_amount)


register = template.Library()


class Node(template.Node):
    def __init__(self, request, func, var_name):
        self.request = request
        self.var_name = var_name
        self.func = func

    def render(self, context):
        try:
            request = self.request.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        result = self.func(request)

        if self.var_name:
            context[self.var_name] = result
            return ''

        return result


def get_currency_from_request(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]

    m = re.search(r'(.*?) as (\w+)', arg)

    if not m:
        raise template.TemplateSyntaxError, "%s tag had invalid arguments" % tag_name

    request, var_name = m.groups()

    return Node(request, get_currency, var_name)


def get_language_from_request(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%s tag requires arguments" % token.contents.split()[0]

    m = re.search(r'(.*?) as (\w+)', arg)

    if not m:
        raise template.TemplateSyntaxError, "%s tag had invalid arguments" % tag_name

    request, var_name = m.groups()

    return Node(request, get_language, var_name)


@register.simple_tag(takes_context=True)
def my_tag(context, from_currency, to_currency,
           amount, ceil, asvar=None, *args, **kwargs):
    output = convert_amount(from_currency, to_currency, amount, ceil=ceil)

    if asvar:
        context[asvar] = output
        return ''

    return output
