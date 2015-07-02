""" Web Service SOAP API functions for firestorm app of project ten. """
from BeautifulSoup import BeautifulStoneSoup
import base64
import datetime
import logging
import os
from random import random, randrange
import re

from common.custom_cleaning import clean_phone_number
from common.utils import create_unique_datetime_str
from django.conf import settings
from django.core.exceptions import ValidationError
from suds import WebFault
from suds.client import Client
from suds.sax.element import Element
from suds.sax.attribute import Attribute

from email_gateway.send import send_admin_email
from firestorm.models import AdRep, AdRepOrder

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)

#logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.ERROR)
logging.getLogger('suds.transport').setLevel(logging.ERROR)
logging.getLogger('suds.xsd.schema').setLevel(logging.ERROR)
logging.getLogger('suds.wsdl').setLevel(logging.ERROR)

TEST_MODE = False

class FirestormSoap(object):
    """ Firestorm Soap methods and parameters. """
    token = 'Q5bU&e#owXuZ'
    context = 'STRAUS'
    base_url = 'https://www.firestormwebservices.com/firestormwebservices/'
    soap_order_url = base_url + 'firestormorderws.asmx'
    soap_dealer_url = base_url + 'firestormdealerws.asmx'
    soap_enroll_url = base_url + 'firestormenrollmentws.asmx'
    soap_genealogy_url = base_url + 'firestormgenealogyws.asmx'
    dealer_url = "http://my10coupons.com"
    dealer_api = "/MemberToolsDotNet/Utils/ReturnDealerImage.aspx?DealerID="    
    firestorm_master_id = 43096
    shipping_code = 'PAID-SHIP'
    payment_type_code = 'PAYOFFSITE'
    catalogue_id = 207 # Distributor
    enrollment_catalogue_id = 206
    customer_type = 'REF CONSUMER'
    WEB_PHOTO_PATH = '%s/media/dynamic/images/ad-rep/' % settings.PROJECT_PATH
    
    def __init__(self, sandbox_mode=False):
        """ Allow web service to connect to live or test server. """
        if sandbox_mode:
            self.context = 'SANDBOX'
            self.catalogue_id = 195
            self.customer_type = 'RETAIL'
      
    def connect(self, soap_url):
        """ Firestorm connect to Soap API. """
        LOG.debug('Connect to: %s' % soap_url)
        self.client = Client(soap_url+'?wsdl', location=soap_url)
    
    def get_dealer_detail(self, firestorm_id, refresh_minutes=None):
        """ Get dealer detail (aka ad rep) from the Firestorm SOAP API. This 
        web service method will not update ad rep rank. """
        # Modify this function to be called with ad_rep firestorm id not ad_rep
        try:
            ad_rep = AdRep.objects.get(firestorm_id=firestorm_id)
        except AdRep.DoesNotExist:
            ad_rep = None 
        LOG.debug('GetDealerDetail, firestorm id: %s' % firestorm_id)
        LOG.debug('GetDealerDetail, refresh_minutes: %s' % refresh_minutes)
        if (refresh_minutes and ad_rep and ad_rep.mailing_address1
            and ad_rep.ad_rep_modified_datetime + datetime.timedelta(
            minutes=refresh_minutes) > datetime.datetime.now()):
            LOG.debug('Ad_rep details not updated')
            return
        response = self.call_get_dealer_detail(firestorm_id)
        if not response:
            LOG.error('Error with get dealer web service')
            return
        response_dict = dict(response)
        if response_dict['diffgram'][0] == '':
            LOG.error('No Dealer found')
            return
        dealer_dict = dict(
            response_dict['diffgram'][0]['DocumentElement'][0]['Dealer'][0])
        ad_rep_dict = {}
        # map the firestorm fields to the ad rep model fields
        field_name_dict = {'EmailPrimary': 'email', 
            'MailAddress1': 'mailing_address1', 
            'MailAddress2': 'mailing_address2',
            'MailCity': 'mailing_city',
            'MailState': 'mailing_state_province', 
            'MailZip': 'mailing_zip_postal', 
            'Password': 'password', 
            'DealerID': 'firestorm_id',
            'DealerURL': 'url',
            'Firstname': 'first_name',
            'LastName': 'last_name',
            'CompanyName': 'company',
            'CellPhone': 'cell_phone_number',
            'FaxPhone': 'fax_phone_number',
            'WorkPhone': 'work_phone_number',
            'HomePhone': 'home_phone_number',
            'StructureSponsoringDealerID': 'sponsor_id'
            }
        for firestorm_field, ad_rep_field in field_name_dict.items():
            try:
                if firestorm_field == 'StructureSponsoringDealerID':
                    # The sponsorID comes in on 2 different field names
                    # for referring ad reps vs ad rep advertisers.
                    dealer_dict[firestorm_field] = [dealer_dict.get(
                        'StructureSponsoringDealerID', 
                        dealer_dict.get('SponsoringDealerID',''))[0].strip()]
                    firestorm_field = 'StructureSponsoringDealerID'
                ad_rep_dict[ad_rep_field] = \
                    dealer_dict[firestorm_field][0].strip()
                if 'phone' in ad_rep_field:
                    ad_rep_dict[ad_rep_field] = clean_phone_number(
                        ad_rep_dict[ad_rep_field])
            except KeyError:
                # firestorm sentinal = test
                LOG.error('GetDealerDetail, firestorm id: %s, field: %s' % (
                    firestorm_id, firestorm_field))
                return
            if (ad_rep and ad_rep_field not in ['password', 'email',
                'sponsor_id']):
                setattr(ad_rep, ad_rep_field, ad_rep_dict[ad_rep_field])
        return self.process_get_dealer_detail(ad_rep, ad_rep_dict, firestorm_id, 
            dealer_dict)
        
    def process_get_dealer_detail(self, ad_rep, ad_rep_dict, firestorm_id, 
        dealer_dict):   
        """ Take the new converted data from firestorm and process it a bit 
        more for password, web photo, ad rep parent, zip. """ 
        ad_rep_dict['web_greeting'] = '' # this field required for connector
        LOG.debug(ad_rep_dict)
        if (str(ad_rep_dict['firestorm_id']) != str(firestorm_id) or
            ad_rep_dict['url'] == ''):
            LOG.error('Invalid Dealer, ID: %s' % firestorm_id)
            return
        if not ad_rep: # do this only for new ad reps, return ad_rep url
            return ad_rep_dict
        if re.match(re.compile("\d{5}(-\d{4})?"), ad_rep.mailing_zip_postal):
            ad_rep.mailing_zip_postal = ad_rep.mailing_zip_postal.replace(
                '-', '')[:9]
        ad_rep.consumer_zip_postal = ad_rep.mailing_zip_postal[:5]
        if ad_rep_dict['password'] != '':
            ad_rep.set_password(ad_rep_dict['password'])
            LOG.debug('GetDealerDetails password updated ID: %s' % (
                ad_rep_dict['firestorm_id']))
        ad_rep.web_photo_path = self.get_ad_rep_web_photo(firestorm_id, 
            dealer_dict)
        ad_rep.save()
        set_ad_rep_parent(
            {ad_rep_dict['firestorm_id']: ad_rep_dict['sponsor_id']})
        LOG.debug('GetDealerDetail Success, firestorm id: %s' % firestorm_id)

    def get_ad_rep_web_photo(self, firestorm_id, dealer_dict):
        """ Decode web photo string, compare string against existing web photo 
        files and return web photo path. Create a new web photo file only if 
        image doesn't exist.
        """
        web_photo_path = None
        try:
            web_photo_encoded = dealer_dict['WebPhoto'][0]
            if web_photo_encoded != '':
                unique_datetime_str = create_unique_datetime_str()
                web_photo_full_path = (self.WEB_PHOTO_PATH + 
                    str(firestorm_id) + '_' + unique_datetime_str + 
                    '.jpg')
                LOG.debug(web_photo_full_path)
                decoded_binary_string = base64.b64decode(web_photo_encoded)
                web_photo_path = find_web_photo_match(firestorm_id, 
                    decoded_binary_string) 
                if not web_photo_path:
                    image_file = open(web_photo_full_path, 'wb')
                    image_file.write(decoded_binary_string)
                    image_file.close()
                    web_photo_path = web_photo_full_path
        except KeyError:
            pass
        return web_photo_path
    
    def get_downline_by_dealer_id(self, firestorm_id=43096, dealership_id=1):
        """ Get downline by dealerid, update ad reps with parent, and return
        ad_reps not in database.
        """
        response = self.call_get_downline_by_dealer_id(
            firestorm_id=firestorm_id, dealership_id=dealership_id)
        if response:
            ad_rep_parent_dict = process_downline_by_dealer_id(response)
        else:
            error_message = 'Firestorm get_downline_by_dealer_id error'
            LOG.error(error_message)
            raise ValidationError(error_message)
        firestorm_id_list = set_ad_rep_parent(ad_rep_parent_dict)
        return firestorm_id_list
    
    def call_get_downline_by_dealer_id(self, firestorm_id, dealership_id):
        """ Connect to SOAP API and call GetDownlineByDealerID service. More 
        info is here: http://firestormwebservices.com/firestormwebservices/
        firestormgenealogyws.asmx?op=GetDownlineByDealerID
        """
        if TEST_MODE:
            LOG.debug('get_downline_by_dealer_id not called')
            return
        self.connect(soap_url=self.soap_genealogy_url)
        return self.client.service.GetDownlineByDealerID(
            Token=self.token, Context=self.context, DealerID=firestorm_id,
            DealershipNumber=dealership_id)
    
    def call_get_dealer_detail(self, firestorm_id):
        """ Connect to SOAP API and call GetDealerDetail service. More info is
        here: http://firestormwebservices.com/firestormwebservices/
        firestormdealerws.asmx?op=GetDealerDetail 
        """
        if TEST_MODE:
            LOG.debug('get_dealer_detail not called')
            return
        self.connect(soap_url=self.soap_dealer_url)
        try:
            response = self.client.service.GetDealerDetail(
                Token=self.token, Context=self.context, DealerID=firestorm_id,
                TaxPayerNumber='', FirstName='', LastName='', CompanyName='', 
                PrimaryEmail='', SecondaryEmail='', IsCustomer='')
        except WebFault as e:
            LOG.error(e)
            return
        return response   
    
    def save_order(self, ad_rep_order):
        """ Save a order to the external Firestorm system. Ad Rep Orders 
        must not already be have an existing Firestorm ID. 
        """
        LOG.debug('ad_rep_order: %s' % ad_rep_order)
        order = ad_rep_order.order
        LOG.debug('order: %s' % order)
        firestorm_order_id = ad_rep_order.firestorm_order_id
        if firestorm_order_id:
            LOG.info('Firestorm order already created for this order: %s' 
                % order)
            return
        orders_xml = create_order_detail_xml(order)
        order_dict = validate_order_data(order)
        try:
            response = self.call_save_order(ad_rep_order, orders_xml, 
                order_dict)
        except WebFault as e:
            LOG.error(e)
            raise ValidationError(
                'SaveOrder data error for order: %s error: %s' % (order, e))
        if response:
            process_save_order_response(response, ad_rep_order, order_dict)
        else:
            raise ValidationError('SaveOrder error for order: %s' % order)
        
    def call_save_order(self, ad_rep_order, orders_xml, order_dict):
        """ Save new order in the Firestorm system through the SOAP API. 
        More info is here: https://firestormwebservices.com/
        firestormwebservices/firestormorderws.asmx?op=SaveOrder 
        """
        order = ad_rep_order.order
        if TEST_MODE or settings.FIRESTORM_LIVE is False:
            LOG.info('No firestorm order created')
            return
        self.connect(soap_url=self.soap_order_url)
        return self.client.service.SaveOrder(
            Token=self.token,
            Context=self.context,
            AddlPaymentInfo='',
            AutoshipOrder=0,
            ShipAddress1=order_dict.get('billing_address1', 
                order.billing_record.billing_address1),
            ShipAddress2=order.billing_record.billing_address2,
            ShipCity=order_dict.get('billing_city', 
                order.billing_record.billing_city),
            ShipFirstName=order.billing_record.alt_first_name,
            ShipLastName=order.billing_record.alt_last_name,
            ShipState=order_dict.get('billing_state_province', 
                order.billing_record.billing_state_province),
            ShipZip=order_dict.get('billing_zip_postal', 
                order.billing_record.billing_zip_postal),
            ShipCountry='USA',
            BillAddress1=order_dict.get('billing_address1', 
                order.billing_record.billing_address1),
            BillAddress2=order_dict.get('billing_address2', 
                order.billing_record.billing_address2),
            BillCity=order_dict.get('billing_city', 
                order.billing_record.billing_city), 
            BillFirstName=order.billing_record.alt_first_name, 
            BillLastName=order.billing_record.alt_last_name,
            BillCompanyName=order.billing_record.business.business_name,
            BillState=order_dict.get('billing_state_province', 
                order.billing_record.billing_state_province),
            BillZip=order_dict.get('billing_zip_postal', 
                order.billing_record.billing_zip_postal),
            BillCountry='USA', 
            CatalogueID=self.catalogue_id,
            CustomerDealerID=0,
            DealerID=ad_rep_order.ad_rep.firestorm_id, 
            Email='', 
            OrderDetail=orders_xml, 
            OrderTotalAmt=order.total,
            PaymentTypeCode=self.payment_type_code,
            ShippingAmt=0,
            ShippingCode=self.shipping_code, 
            SoldTo=order.billing_record.business.business_name,
            TaxAmt=order.tax, 
            TotalOrderDiscount='0.00',
            TotalOrderDiscountPercentage='0.00'
            ) 
    
    def enroll_customer(self, ad_rep_dict):
        """ Enroll member in the Firestorm system. Return either firestorm id 
        on success or on failure, the resulting error message(s).
        """
        response = self.call_enroll_customer(ad_rep_dict)
        if response:
            response_dict = process_enrollment(response)
        else:
            raise ValidationError('Enroll Customer error for: %s' % ad_rep_dict)
        return response_dict
        
    def call_enroll_customer(self, ad_rep_dict):
        """ Connect to SOAP API and call EnrollCustomer service. More info is
        here: https://www.firestormwebservices.com/FirestormWebServices/
        FirestormEnrollmentWS.asmx?op=EnrollCustomer?wsdl 
        Called with ad_rep_dict: first_name, last_name, email, phone_number, 
        address1, address2, city, state_province, zip_postal,
        ad_rep_url, password, sponsor_firestorm_id.
        """
        address_default = ' '
        site = ad_rep_dict['site']
        if TEST_MODE or settings.FIRESTORM_LIVE is False:
            LOG.info('No firestorm customer enrolled')
            return
        self.connect(soap_url=self.soap_enroll_url)
        address_dict = {}
        if site.id != 1:
            address_dict = {'state': site.default_state_province.abbreviation,
                'zip': site.default_zip_postal}
        return self.client.service.EnrollCustomer( 
                Token=self.token,
                Context=self.context, 
                FirstName=ad_rep_dict.get('first_name', ''),
                LastName=ad_rep_dict.get('last_name', ''),
                MiddleInitial='',
                CompanyName='',
                MailingAddress1=address_default,
                MailingAddress2=address_default,
                MailingCity=address_default,
                MailingState=address_dict.get('state', 'NY'),
                MailingZip=ad_rep_dict.get('zip_postal', '10570'),
                MailingCountry='USA',
                BillingAddress1=address_default,
                BillingAddress2=address_default,
                BillingCity=address_default,
                BillingState=address_dict.get('state', 'NY'),
                BillingZip=ad_rep_dict.get('zip_postal', '10570'),
                BillingCountry='USA',
                DayPhone='',
                EveningPhone='',
                MobilePhone='', 
                Email=ad_rep_dict.get('email', ''), 
                SponsorMemberID=ad_rep_dict.get('sponsor_firestorm_id', 
                    self.firestorm_master_id),
                Username=ad_rep_dict.get('ad_rep_url', ''),
                WebsitePassword=ad_rep_dict.get('password', ''),
                CustomerType=self.customer_type
                )

    def enroll_member(self, ad_rep_dict):
        """ Enroll member (dealer with a dealship) in the Firestorm system. 
        Return either firestorm id on success or on failure, the resulting 
        error message(s).
        """
        try:
            response = self.call_enroll_member(ad_rep_dict)
        except WebFault as e:
            LOG.error(str(ad_rep_dict) + str(e))
            if not settings.ENVIRONMENT['is_test']:
                send_admin_email(context={
                    'to_email': [admin[1] for admin in settings.ADMINS],
                    'subject': 'Enroll ad rep error',
                    'admin_data': list(sorted(ad_rep_dict.items())) + list(e)
                    })
            response = {}
        if response:
            response_dict = process_enrollment(response)
        else:
            raise ValidationError('enroll member error for: %s' % ad_rep_dict)
        return response_dict
        
    def call_enroll_member(self, ad_rep_dict):
        """ Connect to SOAP API and call EnrollMember service. More info is
        here: https://www.firestormwebservices.com/FirestormWebServices/
        FirestormEnrollmentWS.asmx?op=EnrollMember?wsdl 
        Called with ad_rep_dict: first_name, last_name, email, phone_number, 
        address1, address2, city, state_province, zip_postal, url, password, 
        referring_ad_rep.
        """
        ad_rep_rank = 'ADREP'
        product_number = 'WS'
        tax_payer_number = 'NOSSN' + str(randrange(100000000, 999999999))
        if TEST_MODE or settings.FIRESTORM_LIVE is False:
            LOG.debug('firestorm: enroll_member not called')
            return """<?xml version='1.0' encoding='utf-8' ?>
                <FIRESTORMRESULT><STATUS>SUCCESS</STATUS><ID>%s</ID>
                </FIRESTORMRESULT>""" % int(random() * 10000)
        self.connect(soap_url=self.soap_enroll_url)
        return self.client.service.EnrollMember(
            Token=self.token,
            Context=self.context, 
            FirstName=ad_rep_dict['first_name'],
            LastName=ad_rep_dict['last_name'],
            MiddleInitial='',
            CompanyName=ad_rep_dict.get('company_name', ' '),
            TaxPayerNumber=tax_payer_number,
            MailingAddress1=ad_rep_dict.get('address1', '-'),
            MailingAddress2=ad_rep_dict.get('address2', ' '),
            MailingCity=ad_rep_dict['city'],
            MailingState=ad_rep_dict['state_province'],
            MailingZip=ad_rep_dict['zip_postal'],
            MailingCountry='USA',
            BillingAddress1=ad_rep_dict.get('address1', '-'),
            BillingAddress2=ad_rep_dict.get('address2', ' '),
            BillingCity=ad_rep_dict.get('city', ' '),
            BillingState=ad_rep_dict['state_province'],
            BillingZip=ad_rep_dict['zip_postal'],
            BillingCountry='USA',
            DayPhone=ad_rep_dict['primary_phone_number'],
            EveningPhone=ad_rep_dict['primary_phone_number'],
            MobilePhone='', 
            Email=ad_rep_dict['email'],
            CatalogueID=self.enrollment_catalogue_id,
            ProductNumber=product_number,
            Price=0.00,
            DealershipTypeCode=ad_rep_rank,
            MemberEnrollerID=ad_rep_dict.get('referring_ad_rep', 
                    self.firestorm_master_id),
            MemberEnrollerPosition=1,
            SponsorMemberID=ad_rep_dict.get('referring_ad_rep', 
                    self.firestorm_master_id),
            SponsorPosition=1,
            BinaryPlacementMemberID=ad_rep_dict.get('referring_ad_rep', 
                    self.firestorm_master_id),
            BinaryPlacementPosition=1,
            BinaryPlacementLineage='',
            UniPlacementMemberID=ad_rep_dict.get('referring_ad_rep', 
                    self.firestorm_master_id),
            UniPlacementPosition=1,
            PaymentTypeCode=self.payment_type_code,
            CardAccountNumber='',
            CVV2Code='',
            CardHolderName='',
            CardExpirationMonth='',
            CardExpirationYear='',
            ShippingCode=self.shipping_code,
            ReplicatedWebsiteURL=ad_rep_dict['url'],
            ReplicatedWebsitePassword=ad_rep_dict['password'],
            AddlPaymentInfo=''
            )

def create_order_detail_xml(order):
    """ Create order detail of save order web service. Expect at most one order 
    item for monthly and annual coupon purchase and one to many order items for 
    flyer purchases. Monthly and annual coupon purchases may be discounted. 
    """
    item_count = order.order_items.all().count()
    order_detail = Element('ORDER')
    order_detail.append(Attribute('itemcount', item_count))
    for order_item in order.order_items.all():
        if (order_item.product_id != 1 or 
            (order_item.product_id == 1 and order.total == 0)):
            order_amount = order.total
        else: # for flyers with no promo only
            order_amount = order_item.amount
        order_xml = Element('ORDERDETAIL')
        order_xml.append(Element('PRODUCTNUMBER').setText(
            order_item.product_id)) 
        order_xml.append(Element('PRODUCTQTY').setText(
            order_item.units))
        order_xml.append(Element('PRICEEACH').setText(order_amount))
        order_xml.append(Element('RETAILPRICEEACH').setText(order_amount))
        order_xml.append(Element('WHOLESALEPRICEEACH').setText(order_amount))
        order_xml.append(Element('UPLINEVOLUMEPRICEEACH').setText(order_amount))
        order_xml.append(Element('PSVAMOUNTEACH'))
        order_xml.append(Element('ISFREEPRODUCT').setText('False'))
        order_xml.append(Element('FREESHIPPING').setText('False'))
        order_detail.append(order_xml)
    
    orders_xml = ("<?xml version='1.0' encoding='utf-8'?>" + str(order_detail))
    LOG.debug(orders_xml)
    return orders_xml

def process_enrollment(response):
    """ This function will return either a firestorm dealer id or it will 
    return error messages from web service. 
    """
    response_dict = {}
    if response:
        LOG.debug('firestorm enroll response: %s' % response)
        soup = BeautifulStoneSoup(response)
        LOG.debug(soup.prettify())
        if soup.find('status').string == 'SUCCESS':
            firestorm_id = int(soup.find('id').string)
            LOG.debug("Success: Firestorm ID: %s" % firestorm_id)
            response_dict['firestorm_id'] = firestorm_id
        else:
            error_list = []
            for error_msg in soup.findAll('errormsg'):
                LOG.error('firestorm enroll error: %s ' % error_msg.string)
                if 'username' or 'ODBC' in error_msg.string:
                    error_list.append('url')
                error_list.append(str(error_msg.string))
            response_dict['error_list'] = error_list
    return response_dict

def process_downline_by_dealer_id(response): 
    """ Process downline by dealer id web service response. Return 
    parent_ad_rep_dict = {firestorm_id: parent_firestorm_id}.
    """
    if not response:
        return
    response_dict = dict(response)
    genealogy_dict = response_dict['diffgram'][0]['DocumentElement'][0]['Genealogy']
    dealer_dict = {}
    parent_dict = {}
    for dealer in genealogy_dict: 
        dealer_dict[dealer.WorkDealerID[0]] = dealer.DealershipID[0]
        parent_dict[dealer.WorkDealerID[0]] = dealer.ParentDealershipID[0]
    # Setup reverse lookup of dealer id by dealership id
    inverse_dealer_dict = {}
    for key, value in dealer_dict.items():
        inverse_dealer_dict[value] = key
    ad_rep_parent_dict = {}
    for dealer_id, dealership_id in dealer_dict.items():
        LOG.debug('DealerID %s, DealershipID %s' % (dealer_id, dealership_id))
        try:
            this_dealership_id = parent_dict[dealer_id]
            parent_dealer_id = inverse_dealer_dict[this_dealership_id]
            ad_rep_parent_dict[int(dealer_id)] = int(parent_dealer_id)
            LOG.debug('ParentDealerID: %s' % parent_dealer_id)
        except KeyError:
            pass
    LOG.debug('ad_rep_parent_dict: %s' % ad_rep_parent_dict)
    return ad_rep_parent_dict

def set_ad_rep_parent(ad_rep_parent_dict):
    """ Set the parent ad rep of each ad rep from ad_rep_parent_dict = 
    {firestorm_id: parent_firestorm_id}. Return a list of firestorm ids that 
    are not ad reps in our database yet. 
    """
    firestorm_id_list = []
    for firestorm_id, parent_firestorm_id in ad_rep_parent_dict.items():
        try:
            ad_rep = AdRep.objects.get(firestorm_id=firestorm_id)
            parent_ad_rep = AdRep.objects.get(firestorm_id=parent_firestorm_id)
            ad_rep.parent_ad_rep = parent_ad_rep
            ad_rep.save()
        except AdRep.DoesNotExist:
            firestorm_id_list.append(firestorm_id)
    LOG.debug('firestorm_id_list: %s' % firestorm_id_list)
    return firestorm_id_list 
            
def process_save_order_response(response, ad_rep_order, order_dict):
    """ 
    Validate response from save order soap call. If success, a firestorm
    order id will be saved to the ad_rep order. 
    """
    LOG.debug('SaveOrder Response: %s' % response)
    soup = BeautifulStoneSoup(response)
    LOG.debug(soup.prettify())
    if soup.find('status').string == 'SUCCESS':
        firestorm_order_id = soup.find('id').string
        LOG.debug("Success: Firestorm Order ID: %s" % 
            firestorm_order_id)
        try:
            ad_rep_order = AdRepOrder.objects.get(order=ad_rep_order.order)
            ad_rep_order.firestorm_order_id = int(firestorm_order_id)
            ad_rep_order.save()
        except ValueError:
            LOG.error("Invalid Firestorm Order ID: %s" % firestorm_order_id)
    else:
        LOG.error('AdRepOrder %s order_dict: %s' % (ad_rep_order.order, 
            order_dict))
        errors = ''
        for error_msg in soup.findAll('errormsg'):
            LOG.error(error_msg.string)
            errors += error_msg.string + '. '
        error_message = 'SaveOrder: %s error: %s' % (ad_rep_order.order, 
            errors)
        LOG.error(error_message)
        raise ValidationError(error_message)

def validate_order_data(order):
    """ Create default values to be sent in order xml since web service 
    doesn't accept blanks. 
    """
    order_dict = {}
    billing_record = order.billing_record
    site = billing_record.business.advertiser.site
    if (not billing_record.billing_address1 or 
        billing_record.billing_address1 == ''):
        order_dict['billing_address1'] = ' '
    if (not billing_record.billing_address2 or 
        billing_record.billing_address2 == ''):
        order_dict['billing_address2'] = ' '
    if not billing_record.billing_city or billing_record.billing_city == '':
        order_dict['billing_city'] = ' '
    if (not billing_record.billing_state_province or 
        billing_record.billing_state_province == ''):
        order_dict['billing_state_province'] = \
            site.default_state_province.abbreviation
    if (not billing_record.billing_zip_postal or 
        billing_record.billing_zip_postal == ''):
        order_dict['billing_zip_postal'] = site.default_zip_postal
    return order_dict

def find_web_photo_match(firestorm_id, binary_image,
    web_photo_path=FirestormSoap().WEB_PHOTO_PATH):
    """ Check if ad rep web photo file exists in the folder. Return file if 
    binary string matches file contents.
    """
    LOG.debug('listing files in: %s' % web_photo_path)
    for image_filename in os.listdir(web_photo_path):
        LOG.debug('checking file: %s' % image_filename)
        if image_filename.endswith('.jpg') and image_filename.startswith(
            str(firestorm_id)):
            # open filename and check against binary string
            image_file_path = os.path.join(web_photo_path, image_filename)
            f = open(image_file_path, 'rb')
            binary_image_local = f.read()
            f.close()
            if binary_image_local == binary_image:
                return image_file_path # match found, do nothing
    

class MockSoap(FirestormSoap):
    """ Mock firestorm soap connection to test save order call. """
    
    def call_save_order(self, ad_rep_order, orders_xml, order_dict):
        """ Mock save order soap call returns a firestorm order number. """
        return """<FIRESTORMRESULT><STATUS>SUCCESS</STATUS><ID>1</ID>
            </FIRESTORMRESULT>"""
    
    def call_enrollment(self, ad_rep_dict):
        """ Mock enrollment or customer or member. """
        if (self.context == 'SANDBOX' and 
            ad_rep_dict['email'] == 'foo@example.com'):
            return """<?xml version='1.0' encoding='utf-8' ?>
            <FIRESTORMRESULT><STATUS>FAIL</STATUS><ID>-1</ID>
            <ORDERID>-1</ORDERID><ERRORS errorcount='1'>
            <ERRORMSG>The username supplied is not available for use</ERRORMSG>
            </ERRORS></FIRESTORMRESULT>"""
        return """<FIRESTORMRESULT><STATUS>SUCCESS</STATUS><ID>10</ID>
            <ERRORS errorcount='0'></ERRORS></FIRESTORMRESULT>"""
    
    def call_enroll_customer(self, ad_rep_dict):
        """ Mock enroll customer soap call returns a successful response. """
        return self.call_enrollment(ad_rep_dict)

    def call_enroll_member(self, ad_rep_dict):
        """ Mock enroll member soap call returns a successful response. """
        return self.call_enrollment(ad_rep_dict)
    
    def call_get_dealer_detail(self, firestorm_id):
        """ Mock get dealer detail soap call returns the ad rep details. This 
        test method overrides the soap xml reply. The ad rep rank is not 
        returned here. The sponsor tag is different for referring 
        consumers.  
        """
        sponsor_tag = """<SponsoringDealerID>-1</SponsoringDealerID>
            <StructureSponsoringDealerID>20</StructureSponsoringDealerID>"""            
        try:
            ad_rep = AdRep.objects.get(firestorm_id=firestorm_id)
            if ad_rep.rank == 'CUSTOMER':
                sponsor_tag = '<SponsoringDealerID>20</SponsoringDealerID>'
        except AdRep.DoesNotExist:
            pass
        self.connect(soap_url=self.soap_dealer_url)
        return self.client.service.GetDealerDetail(__inject={'reply':
            """<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            <soap:Body>
            <GetDealerDetailResponse xmlns="http://trinitysoft.net/">
            <GetDealerDetailResult>
            <diffgr:diffgram xmlns:msdata="urn:schemas-microsoft-com:xml-msdata" xmlns:diffgr="urn:schemas-microsoft-com:xml-diffgram-v1">
            <DocumentElement xmlns="">
            <Dealer diffgr:id="Dealer1" msdata:rowOrder="0">
            <DealerID>%s</DealerID><LastName>Smith</LastName>
            <Firstname>John </Firstname><MiddleInitial>C</MiddleInitial>
            <CompanyName>Test Inc</CompanyName>
            <EmailPrimary>newadrep@deleardetail.org</EmailPrimary>
            <ShipAddress1>57 Test Ave</ShipAddress1>
            <ShipAddress2 xml:space="preserve"> </ShipAddress2>
            <ShipCity>Bronx</ShipCity><ShipState>CA</ShipState>
            <ShipZip>10940</ShipZip><ShipCountry>USA</ShipCountry>
            <MailAddress1>57 Test Ave</MailAddress1>
            <MailAddress2 xml:space="preserve"> </MailAddress2>
            <MailCity>Bronx</MailCity><MailState>NY</MailState>
            <MailZip>10940</MailZip><MailCountry>USA</MailCountry>
            <WorkPhone>123-555-1800</WorkPhone>
            <HomePhone>123-555-1786</HomePhone>
            <FaxPhone xml:space="preserve"> </FaxPhone>
            <CellPhone>416-555-1788</CellPhone>
            <Password>test</Password>%s<DealerURL>joeshmoe</DealerURL>
            <WebPhoto>dGhpc2lzdGhldGV4dA==</WebPhoto>
            </Dealer></DocumentElement></diffgr:diffgram>
            </GetDealerDetailResult></GetDealerDetailResponse></soap:Body>
            </soap:Envelope>""" % (firestorm_id, sponsor_tag) 
            })

    def call_get_downline_by_dealer_id(self, firestorm_id, dealership_id):
        """ Mock get get downline by dealer id soap call returns the genealogy. 
        This test method overrides the soap xml reply. """
        self.connect(soap_url=self.soap_genealogy_url)
        return self.client.service.GetDownlineByDealerID(__inject={'reply': 
            """<?xml version="1.0" encoding="utf-8"?>
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
            <soap:Body><GetDownlineByDealerIDResponse xmlns="http://trinitysoft.net/">
            <GetDownlineByDealerIDResult>
            <diffgr:diffgram xmlns:msdata="urn:schemas-microsoft-com:xml-msdata" xmlns:diffgr="urn:schemas-microsoft-com:xml-diffgram-v1">
            <DocumentElement xmlns="">
            <Genealogy diffgr:id="Genealogy1" msdata:rowOrder="0">
            <DealershipID>10</DealershipID>
            <ParentDealershipID>0</ParentDealershipID>
            <WorkDealerID>1</WorkDealerID></Genealogy>
            <Genealogy diffgr:id="Genealogy2" msdata:rowOrder="1">
            <DealershipID>11</DealershipID>
            <ParentDealershipID>10</ParentDealershipID>
            <WorkDealerID>2</WorkDealerID></Genealogy>
            <Genealogy diffgr:id="Genealogy3" msdata:rowOrder="2">
            <DealershipID>12</DealershipID>
            <ParentDealershipID>11</ParentDealershipID>
            <WorkDealerID>55</WorkDealerID></Genealogy>
            </DocumentElement>
            </diffgr:diffgram></GetDownlineByDealerIDResult>
            </GetDownlineByDealerIDResponse></soap:Body></soap:Envelope>"""
            })