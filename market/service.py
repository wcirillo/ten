""" Service functions for market app. """

import datetime

from django.core.cache import cache

from geolocation.models import USZip
from geolocation.service import transform_market_geom
from market.models import Site

def get_geom_list_item(site, mode):
    """ Get the point or geom (respective to mode) for this site. Used by 
    service build_site_directory. Acceptable modes are : marker | geom.
    """
    if mode == "marker":
        try:
            site_coord = USZip.objects.get(
            code=site['default_zip_postal']).coordinate
            geom = [[site_coord.longitude, 
                site_coord.latitude, str(site['name'])]]
        except USZip.DoesNotExist:
            geom = None
    elif mode == "geom":
        poly = transform_market_geom(site['geom'])
        if poly:
            geom = '%s;%s;%s|' % (
                str(poly), str(site['name']), str(site['directory_name']))
        else:
            geom = None
    else:
        geom = None
    return geom

def build_state_market_dict(site):
    """ Service to build state dict of markets. """
    state_dict = {
        'state': str(site['default_state_province__name']),
        'state_url': 
            str(site['default_state_province__name']).lower().replace(' ', '-')
                  }
    market_dict = {
        'domain': site['domain'], 
        'directory_name': site['directory_name']
        }
    return state_dict, market_dict

def get_sorted_state_list(state_dict):
    """ 
    Take the state_dict, make a list of it's state keys, sort the keys 
    alphabetically and replace each state name with dict object.
    """
    state_list = state_dict.keys()
    state_list.sort()
    for index, item in enumerate(state_list):
        state_list[index] = state_dict[item]
    return state_list
    
def build_site_directory(sites=None, build_mode=None):
    """ 
    Return list of dictionaries of sites group by state and list of site marker 
    points.
    Parameter build_mode accepts values:
        None (builds and returns both a dict and a list)
        'states' (only builds state dict)
        'markers' (only builds market coverage)
    """
    if not build_mode:
        build_mode = ['states', 'markers']
    else:
        build_mode = [build_mode]
    state_site_dict = {}
    if 'markers' not in build_mode:
        geom_data = None
    else:
        if sites:
            geom_mode, geom_data = "geom", ''
        else:
            geom_mode, geom_data = "marker", []
    if not sites:
        sites = Site.objects.get_or_set_cache().select_related(
            'default_state_province'
            ).filter(launch_date__lte=datetime.date.today(),
            default_state_province__isnull=False
            ).defer('us_state__geom'
            ).values('id', 'name', 'directory_name', 'domain', 
            'default_zip_postal', 'geom',
            'default_state_province__abbreviation',
            'default_state_province__name').order_by(
            'default_state_province__name', 'domain',
            )
             
    for site in sites:
        if site['id'] != 1:
            if 'states' in build_mode:
                key = site['default_state_province__abbreviation']
                state_dict, market_dict = build_state_market_dict(site)
                try:
                    state_site_dict[key]['market'].append(market_dict)
                except KeyError:
                    state_dict['market'] = [market_dict]
                    state_site_dict.update({key:state_dict})
            if 'markers' in build_mode:
                geom_val = get_geom_list_item(site, geom_mode)
                if geom_val:
                    geom_data += geom_val
    return get_sorted_state_list(state_site_dict), geom_data
         
def get_current_site(request):
    """
    Accepts request and returns site instance from value set by middleware.
    Gets instance from cache if available; else get it dynamically and set 
    cache. Defer geometry fields.
    """
    try:
        request.current_site
    except AttributeError:
        site_id = request.META.get('site_id', 1)
        cache_key = "site-%s" % site_id
        request.current_site = cache.get(cache_key)
        if not request.current_site:
            request.current_site = Site.objects.defer(
                'envelope','geom','point').get(id=site_id)
            cache.set(cache_key, request.current_site)
    return request.current_site

def append_geoms_to_close_sites(close_sites):
    """ Append site geometry each site in list. Return modified list. """
    if close_sites:
        for index, market_dict in enumerate(close_sites):
            geom = cache.get(("site-%s-geom" % market_dict['id']))
            if not geom:
                site = Site.objects.get(id=market_dict['id'])
                geom = site.set_geom()
            close_sites[index]['geom'] = geom
    return close_sites

def check_for_cross_site_redirect(request, zip_postal, redirect_path=None):
    """
    When a user registers with a zip or postal, check if there is a better
    site match than they are on, and if so redirect.
    
    Use this method to try and figure out if the user is on the correct site.
    This method will check if the site is correct or not based on the zip_postal 
    passed in.  If the site is different, modify the redirect path.
    """
    curr_site = site = get_current_site(request)
    sites = list(Site.objects.get_sites_this_zip(code=zip_postal))
    if len(sites) > 0 and curr_site not in sites:
        found_old_path = 0
        if redirect_path:
            redirect_path_list = redirect_path.split('/')
            for path in redirect_path_list:
                if path == curr_site.directory_name:
                    redirect_path_list.remove(path)
                    found_old_path = 1
            redirect_path_list = '/'.join(redirect_path_list)
            if found_old_path and curr_site.id == 1:
                redirect_path_list = '/' + redirect_path_list
        else:
            redirect_path_list = ''
        site = sites[0]
        redirect_path = 'http://%s/%s%s/' % (request.get_host(),  
            site.directory_name, redirect_path_list.rstrip('/'))
    return site, redirect_path, curr_site

def check_for_site_redirect(request, site_id=None, redirect_path=None):
    """
    When a user logs in, for example, check if they are on the correct site.
    
    Use this method to try and figure out if the user is on the correct site.
    This method will check if the site is correct or not based on the site_id 
    passed in.  If the site is different, modify the redirect path.
    
    site_id = The site you want to be redirected to.
    """
    curr_site = get_current_site(request) # The site you are on.
    if site_id and site_id != 1 and curr_site.id != site_id:
        site = Site.objects.get(id=site_id)
        if redirect_path:
            if curr_site.id == 1:
                # Don't prepend the correct dir if its already there.
                if redirect_path.split('/')[1] != site.directory_name:
                    redirect_path = '/' + site.directory_name + redirect_path
            else:    
                # Use the bounding / to make sure we don't find substring
                # matches.
                redirect_path = redirect_path.replace(
                    '/' + curr_site.directory_name + '/', 
                    '/' + site.directory_name + '/')
        else:
            redirect_path = '/' + site.directory_name + '/'
    return curr_site, redirect_path

def get_close_sites(code, miles=100, exclude_site_id=1, max_results=5):
    """ 
    Search for n closest markets within x miles of this zip. The third optional 
    parameter, exclude_site defaults to site 1 (which is always excluded
    because it has no geometry values), but is meant to exclude the current site
    from the list when it is known and unwanted in the result (how-it-works 
    page), ie: "get sites close to me."
    """
    site = Site.objects.get(id=exclude_site_id)
    return site.close_sites(code=code, miles=miles, max_results=max_results)

def get_markets_in_state(state):
    """ Return list of markets residing in state (passed in). """
    state_name = state.replace('-', ' ').strip()
    sites = Site.objects.filter(
        default_state_province__name__iexact=state_name).values(
            'id', 'name', 'directory_name', 'domain', 
            'default_zip_postal', 'geom',
            'default_state_province__abbreviation',
            'default_state_province__name').order_by(
            'default_state_province__name', 'domain',
            )
    return sites

def get_or_set_market_state_list():
    """ Get or set the state_site_list in/from the cache. """
    state_site_list = cache.get('site-state-list')
    if not state_site_list:
        state_site_list = build_site_directory(build_mode='states')[0]
        cache.set(("site-state-list"), state_site_list)
    return state_site_list

def get_or_set_site_markers():
    """
    Get or set the list of market centroids to display markers) in/from the 
    cache.
    """
    market_markers = cache.get('site-markers')
    if not market_markers:
        market_markers = build_site_directory(build_mode='markers')[1]
        cache.set(('site-markers'), market_markers)
    return market_markers

def strip_market_from_url(url_path):
    """ Remove the first directory of this path (likely generated from reverse)
    if it is a market directory. Useful for instance of passing url path to
    firestorm join-me url.
    """
    # Trim pre and post slashes and format as list to get first directory.
    url_list = url_path.lstrip('//').rstrip('//').split('/')
    try:
        Site.objects.get(directory_name=url_list.pop(0))
        # Don't return leading slash, this is going to be concatenated to a URL.
        return "%s/" % "/".join(url_list)
    except Site.DoesNotExist:
        return url_path.lstrip('//')