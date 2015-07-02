""" This file has the SugarCRM web service integration feed functions """

import hashlib
import logging
import time

from django.core.exceptions import ValidationError
from suds.client import Client
from xml.sax import SAXParseException

from feed import config 

LOG = logging.getLogger('ten.%s' % __name__)
LOG.setLevel(logging.ERROR)

logging.getLogger('suds.client').setLevel(logging.ERROR)
logging.getLogger('suds.transport').setLevel(logging.ERROR)
logging.getLogger('suds.xsd.schema').setLevel(logging.ERROR)
logging.getLogger('suds.wsdl').setLevel(logging.ERROR)

def set_sugar_email_query(module, email): 
    """ return sugar email query for SOAP call """
    return "%s.id in (SELECT eabr.bean_id" % str.lower(module) + \
        " FROM email_addr_bean_rel eabr" + \
        " JOIN email_addresses ea ON (ea.id = eabr.email_address_id)" + \
        " WHERE eabr.deleted=0 AND ea.email_address = '%s')" % email 

def get_sugar_module_fields(sugar, module):
    """ 
    For this Sugar module, get field names. Possible modules: Accounts, 
    Contacts.
    """
    field_list = []
    response = sugar.get_module_fields(module)
    for field in response['module_fields']: 
        field_list.append(field.name)
    return field_list 

def select_sugar_module_fields(module):
    """ 
    Get Sugar module fields that were added from 10coupons for use in 
    get_entry_list query.  
    """
    LOG.info('select_sugar_module_fields: %s' % module)
    if str.lower(module) == "accounts":
        return ['id', 'business_id_c', 'email1', 'name', 'phone_office', 
            'date_modified', 'modified_by_name', 'website', 
            'biz_admin_url_c']
    else: # Contacts
        return ['id', 'advertiser_id_c', 'email1', 'primary_address_street',  
            'primary_address_city', 'primary_address_postalcode', 
            'primary_address_state', 'first_name', 'last_name', 
            'date_modified', 'modified_by_name', 'phone_work', 
            'advertiser_admin_url_c']

def dict_to_name_value(values_dict):
    """
    Takes a dictionary and prepare it for soap and returns a name value 
    formatted list of dictionaries. Used by web call: set_entry.
    """
    LOG.debug('dict_to_name_value')
    #LOG.debug('values_dict = %s' % values_dict)
    name_value_list = []
    for key, value in values_dict.items():
        name_value_list.append({'name': key, 'value': value})
    LOG.debug('name_value_list = %s' % name_value_list)
    return name_value_list

def name_value_to_dict(name_value_dict):
    """
    Takes a get_entry_list response of name value tuples 
    and returns a dictionary. Example:
    Arg: {('name', business_id_c): ('value', 131)}
    Returns: {business_id_c: 131}
    """
    #LOG.debug('name_value_dict = %s' % name_value_dict)
    replace_char_dict = {"&lt;": "<", "&gt;": ">", '&quot;': '"', "&#039;": "'"}
    values_dict = {}
    for key, value in name_value_dict.items():
        if value[1]:
            try:
                float(value[1])
                values_dict[key[1]] = value[1]
            except ValueError:
                unencoded_value = value[1]
                for escaped, unescaped in replace_char_dict.items():
                    unencoded_value = unencoded_value.replace(escaped, 
                        unescaped)     
                values_dict[key[1]] = unencoded_value.replace("&amp;", "&")
        else:        
            values_dict[key[1]] = value[1]
    LOG.debug('values_dict = %s' % values_dict)
    return values_dict

def error_check_response(sugar, response):
    """ Check this sugar web service response for error. """
    if str(response).find('No Error') == -1:
        LOG.error(response)
        sugar.logout()
    else:
        LOG.info('success')
    return


class Sugar():
    """ 
    This class will allow API communication with the Sugar web service 
    by creating and managing sessions, login, and logout of users plus access 
    of web service methods. When TEST_MODE = True, local testing will occur 
    without connecting to the external Sugar web service.
    """
    def __init__(self, web_service_url=config.SUGAR_URL):
        """ Create a Sugar session for this user """
        if config.TEST_MODE:
            self.session = None
            self.response = 'No Error'
        else:    
            self.application = '10Coupons'
            self.web_service_url = web_service_url
            LOG.debug(web_service_url)     
    
    def login(self, username=config.SUGAR_USERNAME, 
        password=config.SUGAR_PASSWORD):
        """ login to web service and return session """
        LOG.debug("login sugar: %s" % username)
        LOG.debug(self.web_service_url)
        self.client = Client(self.web_service_url, 
            location=self.web_service_url)
        if len(password) != 32:
            password = hashlib.new(password).hexdigest()
            LOG.debug("hash created")
        #LOG.debug(password)
        auth = self.client.factory.create("user_auth")
        auth.user_name = username
        auth.password = password
        auth.version = "1.1"
        self.session = self.client.service.login(auth, self.application)
        LOG.info('session id = %s' % self.session.id)
        if self.session.error.name == 'Invalid Login':
            LOG.error(self.session.error.name)
            raise ValidationError(self.session.error.name) 
        return self.session

    def validate_login(self):
        """ validate login session by calling api """
        if config.TEST_MODE:
            return
        try:
            if (self.session and self.client.service.get_user_id(
                self.session.id) == '-1') or self.session is None:
                LOG.error("no session")
                self.logout()
        except SAXParseException:
            LOG.error("Sugar session error")
            time.sleep(5)
            self.login()
        except AttributeError:
            LOG.debug("Sugar session not found")
            self.login()
        return
        
    def logout(self):
        """ logout session """
        LOG.debug("logout sugar")
        if self.session:
            self.client.service.logout(self.session.id)
            self.session = None
        return

    def set_relationship(self, relationship):
        """ wrapper for sugar api call: set_relationship """
        if config.TEST_MODE:
            return self.response
        else:
            self.validate_login()
            response = self.client.service.set_relationship(self.session.id, 
                relationship)
            error_check_response(self, response)
            return response
    
    def get_relationships(self, module_name, module_id, related_module):
        """ wrapper for sugar api call: get_relationships """
        if config.TEST_MODE:
            return self.response
        else:
            self.validate_login()
            response = self.client.service.get_relationships(self.session.id, 
                module_name, module_id, related_module)
            error_check_response(self, response)
            return response
    
    def set_entry(self, module, name_value_list):
        """ wrapper for sugar api call: set_entry """
        LOG.debug('set_entry')
        if config.TEST_MODE:
            return {'id': []}
        else:
            self.validate_login()
            response = self.client.service.set_entry(self.session.id, module, 
                name_value_list)
            error_check_response(self, response)
            return response
    
    def get_entry_list(self, module, query, order_by='', args_dict=None):
        """ wrapper for sugar api call: set_entry_list """
        LOG.debug('get_entry_list')
        LOG.debug('query: %s' % query)
        LOG.debug('order_by: %s' % order_by)
        if config.TEST_MODE:
            return None
        else:
            if args_dict is None:
                args_dict = {}
            LOG.debug('args_dict: %s' % str(args_dict))
            offset = args_dict.get('offset', 0) # record start offset
            selection = args_dict.get('selection', 
                select_sugar_module_fields(module)) # list of fields
            max_result = args_dict.get('max_result', 1) # return 1 entry max
            deleted = args_dict.get('deleted', 0) # hide deleted entries
            LOG.debug('selection: %s' % selection)
            LOG.debug('max_result: %s' % max_result)
            self.validate_login()
            try:
                response = self.client.service.get_entry_list(self.session.id, 
                    module, query, order_by, offset, selection, max_result, 
                    deleted)
                error_check_response(self, response)
                LOG.debug('get_entry_list: result_count = %s' % 
                    response['result_count'])
                if response['result_count'] > 0:
                    sugar_list = []
                    for index in range(response['result_count']):
                        sugar_dict = name_value_to_dict(dict(
                            response['entry_list'][index]['name_value_list']))
                        sugar_list.append(sugar_dict)
                    return sugar_list
            except SAXParseException:
                LOG.error(SAXParseException)
                raise ValidationError(
                    'Check sugar get_entry_list query: %s' % query)
            return None
    
    def get_module_fields(self, module):
        """ wrapper for sugar api call: get_module_fields """
        if config.TEST_MODE:
            return self.response
        else:
            self.validate_login()
            return self.client.service.get_module_fields(self.session.id, 
                module)
