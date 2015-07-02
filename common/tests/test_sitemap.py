""" Test case for common utils. """

import datetime
import xml.dom.minidom

from common.test_utils import EnhancedTestCase
from coupon.models import Coupon, SlotTimeFrame


class TestSitemap(EnhancedTestCase):
    """ Tests for common utils of project ten. """
    fixtures = ['test_advertiser', 'test_coupon', 'test_slot', 'test_flyer']
    
    def test_sitemap(self):
        """ Assert the sitemap is valid request, and valid XML. """
        now = datetime.datetime.now()
        delta = datetime.timedelta(weeks=520)
        for coupon in Coupon.objects.all():
            coupon.start_date = now - datetime.timedelta(1)
            coupon.expiration_date += delta
            coupon.save()
            try:
                slot_time_frame = SlotTimeFrame.objects.filter(
                    coupon=coupon).latest('slot__end_date')
                slot_time_frame.slot.end_date += delta
                slot_time_frame.slot.save()
            except SlotTimeFrame.DoesNotExist:
                pass
        response = self.client.get('/sitemap.xml')
        self.assertEquals(response.status_code, 200)
        self.assertTrue(xml.dom.minidom.parseString(response.content))
        # All local market home pages.
        self.assertContains(response, '/hudson-valley/</loc>')
        self.assertContains(response, '/triangle/</loc>')
        self.assertContains(response, '/capital-area/</loc>')
        # Local market pages canonicalized to site 2.
        self.assertContains(response, '/hudson-valley/how-it-works/</loc>')
        self.assertContains(response, '/hudson-valley/contact-us/</loc>')
        # Current coupons.
        self.assertContains(response, 
            '/hudson-valley/coupon-test14-biz-off-dine/300/</loc>')
        self.assertContains(response, 
            '/hudson-valley/coupon-phillips-toolshed-lot-stuff/411/</loc>')
        # All coupons this biz.
        self.assertContains(response,'/hudson-valley/coupons/bulk/1/</loc>')
        self.assertContains(response, 
            '/hudson-valley/coupons/phillips-toolshed/113/</loc>')
        # Pages that only exist on site 1.
        self.assertContains(response, '/media-partner-home/</loc>')
        self.assertContains(response, '/inside-radio/</loc>')

