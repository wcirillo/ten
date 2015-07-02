""" Test cases for the blog """

from common.test_utils import EnhancedTestCase

class TestBlog(EnhancedTestCase):
    """ Tests for the blog. """
    
    def test_blog(self):
        """ Test for the blog. """
        response = self.client.get('/blog/', follow=True) 
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'zinnia/base.html')
        
        