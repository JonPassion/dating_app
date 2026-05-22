from django import template

from ..utils import display_name

register = template.Library()


@register.filter
def comma_split(value):
    if not value:
        return []
    return [part.strip() for part in value.split(',') if part.strip()]


@register.simple_tag
def user_display_name(user, viewer, is_matched=False):
    return display_name(user, viewer, is_matched=is_matched)
