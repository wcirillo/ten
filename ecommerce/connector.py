""" Classes for connecting to ecommerce gateways for processing payments. """

import datetime
from decimal import Decimal
import logging
import pycurl
import time
import urllib
import urllib2

from BeautifulSoup import BeautifulStoneSoup
from esapi.exceptions import EncryptionException
from suds.sax.element import Element

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import QueryDict

from common.utils import CurlBuffer
from ecommerce.models import Payment, PaymentResponse

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.INFO)
LOG.info('Logging Started')

class BaseConnector(object):
    """ A default connector to ecommerce gateways. Born to be subclassed. """
    test_mode = False
    
    def send_payment(self, order, amount, credit_card, billing_record):
        """ Process a payment for an order through an ecommerce gateway.

        Method should work for both test_mode = True or False.

        Method needs to return a response.
        """
        raise NotImplementedError

    def process_payment(self, order, amount, credit_card, billing_record):
        """
        Process a credit card payment through an ecommerce gateway, creating a
        payment and a payment_response.

        Amount must be a number, not a string.
        Amount can be up to or equal the outstanding balance of order.total.

        credit_card instance may have a key cvv2, which is not a model field.
        """
        amount = Decimal(amount)
        outstanding_balance = order.get_outstanding_balance()
        if amount > outstanding_balance:
            error_message = """Trying to process payment of %s, for order %s
                which has an outstanding balance of %s. Giving up.""" % (
                amount, order.id, outstanding_balance)
            LOG.error(error_message)
            raise ValidationError(error_message)
        # Save payment, status pending.
        payment = Payment.objects.create(order=order, credit_card=credit_card,
            amount=amount, method='C', status='p')
        LOG.debug('saved new payment %s' % payment.id)
        response = self.send_payment(order, amount, credit_card, billing_record)
        payment_response = self.process_payment_response(payment, response)
        # Update payment status.
        payment.status = payment_response.status
        payment.save()
        if payment_response.status != 'A':
            raise ValidationError(payment_response.error_description)
        return payment

    def process_payment_response(self, payment, response):
        """ Process a gateway's response to a payment for an order.

        response is whatever is returned by this payment gateway. It is used
        to construct a payment_response."""
        raise NotImplementedError


class USAePayConnector(BaseConnector):
    """ A connector to the payment gateway of USAePay. """

    def send_payment(self, order, amount, credit_card, billing_record):
        """ Send the payment info to USAePay and receive response. """
        # UMKey: The source key (assigned when you create source in virtual
        # terminal).
        live_data = {
            'gateway_url': 'https://www.usaepay.com/secure/gate.php',
            'UMKey': '24uQ5xn3LGv9Rl8u8NbU7u9zcRW8tU13'
        }
        test_data = {
            'gateway_url': 'https://sandbox.usaepay.com/secure/gate.php',
            'UMKey': '9G1L8vGP3tcvsGb075j2Sev7j99PvY41'
        }
        # Modules can use gateway_data, or test_data directly.
        gateway_data = live_data
        if self.test_mode or settings.DEBUG:
            gateway_data = test_data
        # Get all the stuff USAePay needs.
        data = {'UMkey': gateway_data['UMKey']}
        try:
            data['UMcard'] = credit_card.decrypt_cc()
        except EncryptionException:
            raise ValidationError('Credit card number not valid.')
        try:
            # Saved on the instance but not the model
            data['UMcvv2'] = credit_card.cvv2
        except AttributeError:
            # This is allowed for autorenewal, since CVV2 is never stored.
            pass
        data['UMexpir'] = '%02d%02d' % (int(credit_card.exp_month),
            int(credit_card.exp_year)) # These digits got padding.
        data['UMamount'] = amount
        data['UMinvoice'] = order.invoice
        data['UMponum'] = order.purchase_order
        data['UMname'] = credit_card.card_holder
        data['UMstreet'] = billing_record.billing_address1
        data['UMzip'] = billing_record.billing_zip_postal
        # Pass it to gateway.
        buff = CurlBuffer()
        curl = pycurl.Curl()
        curl.setopt(curl.URL, gateway_data['gateway_url'])
        curl.setopt(curl.POST, 1)
        curl.setopt(curl.POSTFIELDS, urllib.urlencode(data))
        curl.setopt(curl.NOPROGRESS, 1)
        curl.setopt(curl.WRITEFUNCTION, buff.body_callback)
        curl.setopt(curl.VERBOSE, 0)
        curl.perform()
        # Treat content as a QueryDict object for easy parsing
        response = QueryDict(buff.content)
        LOG.debug('Response: %s' % response)
        return response

    def process_payment_response(self, payment, response):
        """  Parse and save a payment response. """
        LOG.debug('Processing payment response: %s' % payment)
        payment_response = PaymentResponse()
        payment_response.payment = payment
        payment_response.status = response['UMstatus'][0] # First letter
        payment_response.reference_number = response.get('UMrefNum', '')
        payment_response.batch = response.get('UMbatch', '')
        if response['UMerrorcode'] != '00000':
            payment_response.error_description = response['UMerror']
        payment_response.avs_result_code = response.get('UMavsResultCode', '')
        try:
            # First letter.
            payment_response.cvv2_result_code = response.get(
                'UMcvv2Result', '')[0]
        except IndexError:
            pass
        if response.get('UMconvertedAmount', '') != '':
            payment_response.converted_amount = Decimal(
                response['UMconvertedAmount'])
        if response.get('UMconversionRate','') != '':
            payment_response.conversion_rate = Decimal(
                response['UMconversionRate'])
        if response.get('UMisDuplicate','') == 'Y':
            payment_response.is_duplicate = True
        payment_response.clean()
        payment_response.save()
        LOG.debug('saved new payment response %s' % payment_response.id)
        LOG.debug('payment response status %s' % payment_response.status)
        return payment_response


class ProPayConnector(BaseConnector):
    """ An ecommerce connector to the ProPay gateway. Link to the docs: 
    http://epay.propay.com/pdf/xmldoc.pdf """
    
    def process_payment(self, order, amount, credit_card, billing_record):
        """ For tests, ProPay requires order invoice number to be unique once 
        every 24 hours. """
        if self.test_mode:
            current_time = datetime.datetime.now()
            order.invoice = int(time.mktime(current_time.timetuple()))
        return super(ProPayConnector, self).process_payment(order, amount, 
            credit_card, billing_record)
    
    def send_payment(self, order, amount, credit_card, billing_record):
        """ Process a payment of an order through ProPay gateway. """
        live_data = {
            'gateway_url': 'https://epay.propay.com/api/propayapi.aspx',
            'cert': 'dccd78b3ee441b78603dab7b042f64',
            'account': '31235167'
        }
        test_data = {
            'gateway_url': 'https://xmltest.propay.com/api/propayapi.aspx',
            'cert': '1bbcc9672324a95a9d0d3649714428',
            'account': '30828622'
        }        
        # Modules can use gateway_data, or test_data directly.
        gateway_data = live_data
        if self.test_mode or settings.DEBUG:
            gateway_data = test_data
        xml_request = Element('XMLRequest')
        xml_request.append(Element('certStr').setText(
            gateway_data['cert']))
        xml_request.append(Element('class').setText('partner'))
        xml_trans = Element('XMLTrans')
        xml_trans.append(Element('transType').setText('04')) # charge card
        xml_trans.append(Element('accountNum').setText(gateway_data['account']))
        # amount: Convert decimal dollar to pennies
        xml_trans.append(Element('amount').setText(int(amount*100)))
        xml_trans.append(Element('cardholderName').setText(
            credit_card.card_holder))
        xml_trans.append(Element('addr').setText(
            billing_record.billing_address1))
        xml_trans.append(Element('zip').setText(
            billing_record.billing_zip_postal))
        try:
            xml_trans.append(Element('ccNum').setText(credit_card.decrypt_cc()))
        except EncryptionException:
            raise ValidationError('Credit card number not valid.')
        xml_trans.append(Element('expDate').setText('%02d%02d' % (int(
            credit_card.exp_month), int(credit_card.exp_year))))
        try:
            # Saved on the instance but not the model
            xml_trans.append(Element('CVV2').setText(credit_card.cvv2))
        except AttributeError:
            # This is allowed for autorenewal, since CVV2 is never stored.
            pass
        xml_trans.append(Element('invNum').setText(order.invoice))
        xml_request.append(xml_trans)
        xml_payment = ('<?xml version= "1.0"?><!DOCTYPE Request.dtd>' + 
            str(xml_request))
        # LOG.debug(xml_payment)
        # Pass it to gateway.
        response = self.call_payment_gateway(url=gateway_data['gateway_url'], 
            data=xml_payment)
        LOG.debug('Response: %s' % response)
        return response

    @staticmethod
    def call_payment_gateway(url, data):
        """ Call the payment gateway. """
        request = urllib2.Request(url, data)
        url_file = urllib2.urlopen(request)
        return url_file.read()

    def process_payment_response(self, payment, response):
        """ Process a response to a payment of an order through ProPay gateway.
        """
        LOG.debug('Processing payment response: %s' % payment)
        payment_response = PaymentResponse()
        payment_response.payment = payment
        soup = BeautifulStoneSoup(response)
        LOG.debug(soup.prettify())
        status = soup.find('status').string
        payment_response.status = 'D'
        payment_response.error_description = 'ProPay Status: %s.' % status
        if soup.find('transnum'):
            payment_response.reference_number = str(soup.find('transnum').string)
        if soup.find('avs'):
            payment_response.avs_result_code = str(soup.find('avs').string)
        if soup.find('cvv2resp'):
            payment_response.cvv2_result_code = str(soup.find('cvv2resp').string)
        # Save error text
        status_code_list = [['00', 'Success', 'A'], ['48', 'Invalid CC', 'D'], 
            ['58', 'Decline', 'D'], ['59', 'User Not Authenticated', 'P'], 
            ['61', 'Amount Exceeds Limit', 'P'], 
            ['49', 'Invalid Expiration Date', 'D'],
            ['69', 'Duplicate Invoice', 'P'], ['50', 'Invalid CCV2', 'D'],
            ['62', 'Amount Exceeds Monthly Limit', 'P'], 
            ['81', 'Account Expired', 'P']]
        for status_code, error_description, response_status in status_code_list:
            if status_code == status:
                payment_response.error_description = error_description
                payment_response.status = response_status
                break
        payment_response.clean()
        payment_response.save()
        LOG.debug('saved new payment response %s' % payment_response.id)
        LOG.debug('payment response status %s' % payment_response.status)
        return payment_response

