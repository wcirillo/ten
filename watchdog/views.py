""" Views for watchdog app. """
import datetime
import decimal

from django.core.urlresolvers import reverse
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext

from consumer.models import Consumer
from common.decorators import superuser_required
from market.models import Site
from watchdog.models import SiteHealth

def site_health(request, action=None, data=None):
    """
    Method to test health of the site.  
    
    Currently takes 'data' checks for length and writes it to the db with a 
        unique timestamp (now).  Reads the value stored for timestamp 'now',
        deletes the record, and returns the value to the caller.
        
        called from the outside world, this tests
            network connectivity
            nginx functionality
            apache functionality
            django functionality
            database connectivity
            ability to read and write from/to the database            
    """
    fakey = "Segmentation fault<br>bash#"
    now = datetime.datetime.now()
    if len(action) > 50 or len(data) > 50:
        if settings.DEBUG == False:
            return HttpResponse(fakey)
        else:
            return HttpResponseRedirect(reverse('all-coupons'))
    if action:
        writetoken = SiteHealth.objects.create(datestamp=now)
        writetoken.extra = data
        writetoken.save()    
        try:
            readtoken = SiteHealth.objects.get(datestamp=now)
            checkdata = readtoken.extra            
        except SiteHealth.DoesNotExist:
            return HttpResponse('Failed to retrieve health record with ' 
                'timestamp %s' % (now))
        if checkdata == data:
            try:
                extra = readtoken.extra
                readtoken.delete()
                return HttpResponse(extra)
            except Exception:
                return HttpResponse(
                    'Failed to delete record for %s with data %s' % 
                        (now, checkdata))
        else:
            return HttpResponse('Retrieved healh record for %s, expecting data'
                    ' "%s", but got "%s"' % (now, data, checkdata))


@superuser_required
def get_blast_effect_before(request, sitenum=None, sitename=None, date=None, show_daily=True):
    """
    Facility to take a look at site performance (in terms of consumer signups)
    around a certain day.  Originally developed to guage the effect of an email
    blast by a media partner
    
    example: http://10coupons.com/blast-effects/34/2010-10-07/ 
             http://10coupons.com/blast-effects/hudson/2010-10-07/ 
    """    
    
    try:
        if sitenum:
            site = Site.objects.get(id=sitenum)
        elif sitename:
            site = Site.objects.filter(domain__icontains=sitename)[0]
            sitenum = '%d' % site.id
    except Site.DoesNotExist:
        return render_to_response('display_blast_effects.html')
    except IndexError:
        return render_to_response('display_blast_effects.html')
    if sitenum > '0':
        pre_blast = Consumer.objects.filter(site__id__exact=sitenum, 
            consumer_create_datetime__lt=date).count()
        post_blast = Consumer.objects.filter(site__id__exact=sitenum, 
            consumer_create_datetime__gte=date).count()
        site_total = Consumer.objects.filter(site__id__exact=sitenum).count()
        consumers = Consumer.objects.filter(site__id__exact=sitenum)
        sitenum = "%s gak" % sitenum
    else:
        pre_blast = Consumer.objects.filter(
            consumer_create_datetime__lt=date).count()
        post_blast = Consumer.objects.filter(
            consumer_create_datetime__gte=date).count()
        site_total = Consumer.objects.all().count()
        consumers = Consumer.objects.all()
        sitenum = "%s goo" % sitenum
    days, postdays = 1, 1
    dates = {}
    for consumer in consumers:
        this_date = consumer.consumer_create_datetime.date()        
        consumers_on_this_date = dates.get(this_date)
        if consumers_on_this_date:
            dates[this_date] = consumers_on_this_date + 1
        else:
            dates[this_date] = 1
            if this_date.isoformat() < date:
                days = days + 1
            else:
                postdays = postdays + 1
    daily_stats = []            
    if show_daily:
        for day, signups in sorted(dates.items()):
            if day.isoformat() >= date:
                daily_stats.append("%s  -  %s -  %d" % (day.isoformat(), sitenum, 
                        signups))
    
    decimal.getcontext().prec = 3
    context = {
        'pre_blast_total': pre_blast,
        'pre_blast_site_age_days': days,
        'pre_blast_signups_per_day': 
            (decimal.Decimal(pre_blast) / decimal.Decimal(days)),
        'post_blast_signups': post_blast,
        'post_blast_signups_per_day': 
            (decimal.Decimal(post_blast) / decimal.Decimal(postdays)),
        'total_consumers': site_total,
        'daily_stats': daily_stats,
        'sitenum': sitenum,
        'site': site,
    }
    return render_to_response('display_blast_effects.html', context, 
            context_instance=RequestContext(request))
    
      
