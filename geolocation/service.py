""" Service functions for geolocation app. """
import re

from django.contrib.gis.geos import GEOSGeometry, Point
from django.db import connection

from geolocation.models import USZip, USCity  

def build_county_geometries(site):
    """ Return list of counties and their geometries for this market. """
    county_list = []
    map_coverage = ''
    site_counties = get_consumer_count_per_county(site)
    for county in site_counties:
        county_list.append(county[0])
        poly = transform_market_geom(GEOSGeometry(county[1]))
        if poly:
            map_coverage = map_coverage + str(poly)  + ';' \
                    +  str(county[0]) + ';' + str('directory/') + '|'
    return county_list, map_coverage

def build_zip_geometries(site):
    """ Return list of zips and their geometries for this market. """
    zip_data = ''
    market_zips = USZip.objects.filter(
        us_county__sites__id=site.id
        )
    for _zip in market_zips:
        if _zip.geom:
            poly = transform_market_geom(_zip.geom, simp_start=15)
            if poly:
                zip_data += str(poly)  + ';' + str(_zip.code) + ';;' + \
                str(_zip.id) + '|'
        else:
            zip_data += str(Point(
                _zip.coordinate.longitude, _zip.coordinate.latitude, 
                srid=4326).transform(900913, clone=True)) \
                + ';' + str(_zip.code) + ';;' + str(_zip.id) + '|'
    return zip_data

def build_city_geometries(site):
    """ Return list of cities and their geometries for this market. """
    city_data = ''
    market_cities = USCity.objects.filter(
        us_county__sites__id=site.id
        )
    for city in market_cities:
        if city.geom:
            poly = transform_market_geom(city.geom, simp_start=15)
            if poly:
                city_data += str(poly)  + ';city_' + str(city.name) + ';;' + \
                str(city.id) + '|'
        else:
            city_data += str(Point(
                city.coordinate.longitude, city.coordinate.latitude, 
                srid=4326).transform(900913, clone=True)) \
                + ';city_' + str(city.name) + ';;' + str(city.id) + '|'
    return city_data
        
def check_code_is_valid(code):
    """ Return true if us_zip is valid. """
    is_valid = False
    if re.match("\d{5}$", code):
        try:
            USZip.objects.get(code=code)
            is_valid = True
        except USZip.DoesNotExist:
            pass
    return is_valid

def get_city_and_state(zip_code):
    """ Return city and state for this zip code. """
    us_zip = USZip.objects.filter(code=zip_code
        ).values_list('us_city__name', 'us_state__abbreviation')
    try:
        city = us_zip[0][0]
        state = us_zip[0][1]
    except IndexError:
        city = state = ''
    return city, state

def get_consumer_count_by_city(site, minimum=0):
    """ Return all the cities related to this site, and how many consumers in each.
    """
    cursor = connection.cursor()
    cursor.execute("""
        SELECT ci.name, st.name, COUNT(c.user_ptr_id) AS consumer_count
        FROM geolocation_uscity ci
        JOIN geolocation_usstate st
            ON st.id = ci.us_state_id
        JOIN market_site_us_county s_cn
            ON s_cn.uscounty_id = ci.us_county_id
        JOIN geolocation_uszip z
            ON z.us_city_id = ci.id
        JOIN consumer_consumer c
            ON c.consumer_zip_postal = z.code
        WHERE s_cn.site_id = %s
        GROUP BY ci.name, st.name
        HAVING COUNT(c.user_ptr_id) > %s
        ORDER BY consumer_count DESC, ci.name""", [site.id, minimum])
    return cursor

def get_consumer_count_by_county(us_county):
    """ Given a us county, return count of related consumers. This query is 
    written as raw sql to avoid circular import with Consumer.models.
    """
    cursor = connection.cursor()
    cursor.execute("""
    SELECT COUNT(consumer.user_ptr_id) AS "id__count"
    FROM consumer_consumer consumer
        INNER JOIN geolocation_uszip zip
            ON consumer.geolocation_id = zip.id
        INNER JOIN geolocation_uscounty county
            ON zip.us_county_id = county.id
    WHERE county.id = %s
    """, [us_county.id])
    return cursor.fetchone()[0]

def get_consumer_count_per_county(site):
    """ Group counties in site and return count how many consumers in each.  """
    cursor = connection.cursor()
    cursor.execute("""
        SELECT county.name, county.geom, count(user_ptr_id) as "consumer_count"
        FROM geolocation_uscounty county
            INNER JOIN market_site_us_county market_county_xref
                ON county.id = market_county_xref.uscounty_id
                AND site_id = %s
            INNER JOIN geolocation_uszip zip
                ON zip.us_county_id = county.id
            LEFT JOIN consumer_consumer
                ON consumer_zip_postal = zip.code
        GROUP BY county.name, county.geom
        ORDER BY consumer_count DESC, county.name ASC
        """, [site.id])
    return cursor.fetchall()

def qry_consumer_count_spread(site_id):
    """ Return a current consumer_site count per zip code, includes county and
    city names. """
    cursor = connection.cursor()
    cursor.execute("""
    SELECT geo_county.name AS "county", geo_county.id AS "county_id",
    geo_city.name AS "city", geo_city.id AS "city_id", 
    geo_zip.code AS "zip", geo_zip.id AS "zip_id", COUNT(c.user_ptr_id) AS "zip_count"
    FROM market_site site
        INNER JOIN market_site_us_county market_county
            ON site.id = market_county.site_id
        INNER JOIN geolocation_uscounty geo_county
            ON market_county.uscounty_id = geo_county.id
        INNER JOIN geolocation_uszip geo_zip
            ON geo_county.id = geo_zip.us_county_id
        INNER JOIN geolocation_uscity geo_city 
            ON geo_zip.us_city_id = geo_city.id
        LEFT JOIN 
            (Select c.user_ptr_id, c.consumer_zip_postal, c.site_id,
                c.is_email_verified
             From consumer_consumer c
                 Inner Join consumer_consumer_email_subscription ces
                    On c.user_ptr_id = ces.consumer_id
                        And ces.emailsubscription_id = 1
                        And c.site_id = %(site_id)s
                        And c.is_emailable=True
            ) c
            ON c.consumer_zip_postal = geo_zip.code
            AND c.site_id = site.id
    WHERE site.id = %(site_id)s
    GROUP by geo_county.name, geo_county.id, geo_city.name, geo_city.id, geo_zip.code, geo_zip.id
    ORDER BY geo_county.name, geo_city.name, geo_zip.code""",
    {'site_id': site_id})      
    return cursor.fetchall()

def get_consumer_count_by_zip(us_zip):
    """  Given a us zip, return count of related consumers. This query is 
    written as raw sql to avoid circular import with Consumer.models.
    """
    cursor = connection.cursor()
    cursor.execute("""
    SELECT COUNT(consumer.user_ptr_id) AS "id__count"
    FROM consumer_consumer consumer
        INNER JOIN geolocation_uszip zip
            ON consumer.geolocation_id = zip.id
    WHERE zip.code = %s
    """, [us_zip.code])
    return cursor.fetchone()[0]

def transform_market_geom(geom, default_max=80, simp_max=5000,
        min_points=50, simp_start=35):
    """ Return transformed market geom for map display. """
    simp = simp_start # Smallest possible simp.
    first_poly = geom.transform(900913, clone=True).simplify(simp)
    poly = first_poly
    temp_simp = int(first_poly.num_points * .45)
    market_simp = int(first_poly.num_points * .1)
    while poly.num_points > default_max and temp_simp <= simp_max:
        poly = first_poly.simplify(temp_simp)  
        temp_simp += market_simp
    if poly.num_points < min_points - 5:
        temp_simp -= (int(market_simp * 2))
        while poly.num_points < min_points and temp_simp >= 5:
            poly = first_poly.simplify(temp_simp)
            temp_simp -= market_simp
            if temp_simp < 0 and poly.num_points < min_points:
                if temp_simp <= simp_start - market_simp:
                    temp_simp = 0
                else:
                    temp_simp = simp_start
    # Some geoms cannot be simplified (like Long Island).
    if poly.num_points > min_points:
        return poly
    else:
        return geom.transform(900913, clone=True)