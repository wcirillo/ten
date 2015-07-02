""" 
The file for a dynamic value template tag.  Used originally in create locations.
"""
#pylint: disable=W0613

from django import template
from django.template.base import Library

register = Library()

class DynamicVariableNode(template.Node):
    """ The Node Class for the Dynamic Value Template Tag. """
    def __init__(self, form, field_string, dynamic_string):
        self.form = template.Variable(form)
        self.field_string = field_string
        self.dynamic_string = template.Variable(dynamic_string)

    def render(self, context):
        try:
            form = self.form.resolve(context)
            dynamic_string = self.dynamic_string.resolve(context)
            key = '%s%d' % (self.field_string, dynamic_string+1)
            return form[key]
        except template.VariableDoesNotExist:
            return ''
        
def get_dynamic_value(parser, token):
    """
    This is the name of the template tag to be called for a dynamic variable.
    """
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, form, field_string, dynamic_string = token.split_contents()
    except ValueError:
        tag_name = token.contents.split()[0]
        raise template.TemplateSyntaxError(
            "%r tag requires exactly three arguments" % tag_name)
    return DynamicVariableNode(form, field_string, dynamic_string)
register.tag(get_dynamic_value)



