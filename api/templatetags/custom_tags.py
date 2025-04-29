from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)



register = template.Library()

@register.filter
def get_item(dictionary, key):
    if dictionary:
        return dictionary.get(key)
    return None