""" 
The figure out if a specific class is in this form field.
"""
from django.template import Library

register = Library()

@register.filter
def get_geom_region_class(field):
    """ These fields should have a class which identifies what type of 
        region they are.
        Options are: county, city, or zip
    """
    if 'county' in field.field.widget.attrs['class']:
        return 'county'
    elif 'city' in field.field.widget.attrs['class']:
        return 'city'
    elif 'zip' in field.field.widget.attrs['class']:
        return 'zip'
    else:
        return ''
get_geom_region_class.is_safe = False


@register.filter
def get_region_consumer_count(field):
    """ Get the consumer count for a specific form field  aka regions
    """
    id_ = field.field.widget.attrs['id']
    return id_.split('_')[2]
get_region_consumer_count.is_safe = False


