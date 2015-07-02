""" Views for Adding/Updating an AdReps photo. """

import logging

from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.views.generic.base import TemplateResponseMixin

from firestorm.decorators import ad_rep_required_md
from firestorm.forms import AdRepPhotoUploadForm
from firestorm.models import AdRep

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)
LOG.info('Logging Started')


class AdRepPhotoUpload(TemplateResponseMixin, View):
    """ Class based view for ad rep photo uploads. """
    template_name = 'firestorm/display_ad_rep_photo_upload.html'
    context = {}

    @method_decorator(ad_rep_required_md())
    def dispatch(self, *args, **kwargs):
        return super(AdRepPhotoUpload, self).dispatch(*args, **kwargs)

    def get(self, request):
        """ Handle a GET request of this view. """
        ad_rep = self.prepare(request)
        self.context = {'ad_rep': ad_rep,
            'ad_rep_photo_upload_form': AdRepPhotoUploadForm()}
        return self.render_to_response(RequestContext(request, self.context))
    
    def post(self, request):
        """ Handle a POST request of this view. """
        ad_rep = self.prepare(request)
        ad_rep_photo_upload_form = AdRepPhotoUploadForm(
            request.POST, request.FILES)
        if ad_rep_photo_upload_form.is_valid():
            ad_rep_photo_upload_form.save(request, ad_rep)
        self.context = {'ad_rep': ad_rep,
            'ad_rep_photo_upload_form': ad_rep_photo_upload_form}
        return self.render_to_response(RequestContext(request, self.context))

    @staticmethod
    def prepare(request):
        """ Handle all the preparation for the GET/POST requests """
        ad_rep = AdRep.objects.get(email=request.session['consumer']['email'])
        return ad_rep

