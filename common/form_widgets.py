""" 
This file holds widgets for the forms.  Django's default widgets had specific
css associated with it that we didn't want to use.  So, we wrote our own. 
"""

from itertools import chain

from django.contrib.localflavor.us.us_states import STATE_CHOICES
from django.forms.widgets import SelectMultiple, CheckboxInput, Select, \
    RadioInput
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.encoding import StrAndUnicode, force_unicode

from market.models import Site


class CheckboxSelectMultiple(SelectMultiple):
    """ Form Widget for a multiple select checkbox. """
    def render(self, name, value, attrs=None, choices=()):
        if value is None: 
            value = []
        final_attrs = self.build_attrs(attrs, name=name)
        output = [u'']
        # Normalize to strings
        str_values = set([force_unicode(v) for v in value])
        for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
            # If an ID attribute was given, add a numeric index as a suffix,
            # so that the checkboxes don't all have the same ID attribute.
            if attrs and 'id' in attrs:
                final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
                label_for = u' for="%s"' % final_attrs['id']
            else:
                label_for = ''

            checkbox = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
            option_value = force_unicode(option_value)
            rendered_cb = checkbox.render(name, option_value)
            option_label = conditional_escape(force_unicode(option_label))
            output.append(u'<li>%s <label%s>%s</label></li>' % (rendered_cb, label_for, option_label))
        output.append(u'')
        return mark_safe(u'\n'.join(output))

    def id_for_label(cls, id_):
        # See the comment for RadioSelect.id_for_label()
        if id_:
            id_ += '_0'
        return id_
    id_for_label = classmethod(id_for_label)


class RadioFieldRenderer(StrAndUnicode):
    """
    An object used by RadioSelect to enable customization of radio widgets.
    """

    def __init__(self, name, value, attrs, choices):
        super(RadioFieldRenderer, self).__init__()
        self.name, self.value, self.attrs = name, value, attrs
        self.choices = choices

    def __iter__(self):
        for i, choice in enumerate(self.choices):
            yield RadioInput(self.name, self.value, self.attrs.copy(), choice, i)

    def __getitem__(self, idx):
        choice = self.choices[idx] # Let the IndexError propogate
        return RadioInput(self.name, self.value, self.attrs.copy(), choice, idx)

    def __unicode__(self):
        return self.render()

    def render(self):
        """Outputs a <ul> for this set of radio fields."""
        return mark_safe(u'\n%s\n' % u'\n'.join([u'<li>%s</li>'
                % force_unicode(w) for w in self]))


class RadioSelect(Select):
    """ Radio Button Widget for the forms."""
    renderer = RadioFieldRenderer

    def __init__(self, *args, **kwargs):
        # Override the default renderer if we were passed one.
        renderer = kwargs.pop('renderer', None)
        if renderer:
            self.renderer = renderer
        super(RadioSelect, self).__init__(*args, **kwargs)

    def get_renderer(self, name, value, attrs=None, choices=()):
        """Returns an instance of the renderer."""
        if value is None: 
            value = ''
        str_value = force_unicode(value) # Normalize to string.
        final_attrs = self.build_attrs(attrs)
        choices = list(chain(self.choices, choices))
        return self.renderer(name, str_value, final_attrs, choices)

    def render(self, name, value, attrs=None, choices=()):
        return self.get_renderer(name, value, attrs, choices).render()

    def id_for_label(cls, id_):
        # RadioSelect is represented by multiple <input type="radio"> fields,
        # each of which has a distinct ID. The IDs are made distinct by a "_X"
        # suffix, where X is the zero-based index of the radio field. Thus,
        # the label for a RadioSelect should reference the first one ('_0').
        if id_:
            id_ += '_0'
        return id_
    id_for_label = classmethod(id_for_label)


class USStateSelect(Select):
    """ Form Widget for a State Drop Down with a default value . """
    def __init__(self, attrs=None, site=None):
        state_choices_ = (('', u'- select a state -'),)
        if site and site.id != '1':
            # Place Close Sites on the top of the drop down menu.
            close_sites = site.get_or_set_close_sites()
            if close_sites:
                close_sites_list = []
                dash = (('dash', u'---------------------------------'),)
                for market in close_sites:
                    close_site = Site.objects.get(id=market['id'])
                    item_1 = '%s' % close_site.default_state_province.abbreviation
                    item_2 = '%s' % close_site.default_state_province.name
                    inner_tuple = (item_1, item_2)
                    site_tuple = (inner_tuple,)
                    if site_tuple not in close_sites_list:
                        close_sites_list.append(site_tuple)
                state_choices_ += dash
                for site_tuple in close_sites_list:
                    state_choices_ += site_tuple
                state_choices_ += dash
        state_choices_ += STATE_CHOICES

        super(USStateSelect, self).__init__(attrs, choices=state_choices_)

