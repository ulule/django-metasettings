import re

from django import template
from django.template import TemplateSyntaxError

from metasettings.models import (get_currency_from_request as get_currency,
                                 get_language_from_request as get_language,
                                 get_timezone_from_request as get_timezone,
                                 convert_amount as _convert_amount)


register = template.Library()

kwarg_re = re.compile(r"(?:(\w+)=)?(.+)")


class Node(template.Node):
    def __init__(self, request, func, var_name):
        self.request = template.Variable(request)
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


@register.tag
def get_currency_from_request(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("%s tag requires arguments" % token.contents.split()[0])

    m = re.search(r'(.*?) as (\w+)', arg)

    if not m:
        raise template.TemplateSyntaxError("%s tag had invalid arguments" % tag_name)

    request, var_name = m.groups()

    return Node(request, get_currency, var_name)


@register.tag
def get_language_from_request(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("%s tag requires arguments" % token.contents.split()[0])

    m = re.search(r'(.*?) as (\w+)', arg)

    if not m:
        raise template.TemplateSyntaxError("%s tag had invalid arguments" % tag_name)

    request, var_name = m.groups()

    return Node(request, get_language, var_name)


@register.tag
def get_timezone_from_request(parser, token):
    try:
        tag_name, arg = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError("%s tag requires arguments" % token.contents.split()[0])

    m = re.search(r'(.*?) as (\w+)', arg)

    if not m:
        raise template.TemplateSyntaxError("%s tag had invalid arguments" % tag_name)

    request, var_name = m.groups()

    return Node(request, get_timezone, var_name)


class ConvertAmountNode(template.Node):
    @classmethod
    def parse_params(cls, parser, bits):
        args, kwargs = [], {}
        for bit in bits:
            name, value = kwarg_re.match(bit).groups()
            if name:
                kwargs[name] = parser.compile_filter(value)
            else:
                args.append(parser.compile_filter(value))
        return args, kwargs

    @classmethod
    def handle_token(cls, parser, token):
        bits = token.split_contents()
        name = bits[0]

        if len(bits) < 4:
            raise TemplateSyntaxError("'%s' takes at least 3 argument" % name)

        asvar = None

        if 'as' in bits:
            pivot = bits.index('as')

            try:
                asvar = bits[pivot + 1]
            except IndexError:
                raise TemplateSyntaxError("'%s' arguments must include "
                                          "a variable name after 'as'" % name)
            del bits[pivot:pivot + 2]

        cls_args, cls_kwargs = cls.parse_params(parser, bits[1:])

        cls_kwargs['asvar'] = asvar

        return cls(*cls_args, **cls_kwargs)

    def __init__(self, from_currency, to_currency, amount, ceil=False, asvar=None):
        self.from_currency = from_currency
        self.to_currency = to_currency
        self.amount = amount
        self.ceil = ceil
        self.asvar = asvar

    def render(self, context):
        from_currency = self.from_currency.resolve(context)

        to_currency = self.to_currency.resolve(context)

        amount = self.amount.resolve(context)

        ceil = self.ceil and self.ceil.resolve(context) or self.ceil

        amount = _convert_amount(from_currency,
                                 to_currency,
                                 amount,
                                 ceil=ceil)

        if self.asvar:
            context[self.asvar] = amount
            return ''

        return amount


@register.tag
def convert_amount(parser, token):
    return ConvertAmountNode.handle_token(parser, token)
