""" Views for the Ad Rep Virtual Office to display commissions. """

import logging

from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin

from firestorm.decorators import ad_rep_required_md
from firestorm.models import AdRep

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)
LOG.info('Logging Started')


class AdRepDownline(TemplateResponseMixin, View):
    """ Class based view for an ad reps account to display commissions. """
    template_name = 'firestorm/display_downline_recruits.html'
    context = {}

    @method_decorator(ad_rep_required_md())
    def dispatch(self, *args, **kwargs):
        return super(AdRepDownline, self).dispatch(*args, **kwargs)

    def get(self, request):
        """ Handle a GET request of this view. """
        try:
            ad_rep = AdRep.objects.get(
                id=request.session['consumer']['consumer_id'])
        except (AdRep.DoesNotExist, KeyError):
            return reverse('sign-in')
        child_rep_ids = AdRep.objects.filter(
            parent_ad_rep=ad_rep.id).only('id')
        commissions = AdRep.objects.filter(id__in=child_rep_ids)
        self.context.update({'commissions': commissions,
            'js_ad_rep_recruits': 1})
        return self.render_to_response(RequestContext(request, self.context))



