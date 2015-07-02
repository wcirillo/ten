""" Test forms of common app. """
from django.test import TestCase

from common.forms import SignInForm
from firestorm.factories.ad_rep_factory import AD_REP_FACTORY


class TestSignInForm(TestCase):
    """ Assert form method functionality. """

    def test_invalid_login(self):
        """ Assert invalid credentials are denied. """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        form = SignInForm(data=
            {'email': ad_rep.email, 'password': ''}, test_mode=True)
        self.assertEqual(form.is_valid(), False)
        self.assertEqual(form.errors['email'][0], 
            "Email Address and Password don't match.")

    def test_is_valid(self):
        """ Assert email is trimmed of excessive space and converted to lower
        case when form submission is valid.
        """
        ad_rep = AD_REP_FACTORY.create_ad_rep()
        form = SignInForm(data={
            'email': '    %s  ' % ad_rep.email.upper(),
            'password': 'password'},
            test_mode=True)
        self.assertEqual(form.is_valid(), True)
        self.assertEqual(form.cleaned_data['email'], ad_rep.email)
