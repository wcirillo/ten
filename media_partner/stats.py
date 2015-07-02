"""
Helpers for generating stats about Sites
"""
import datetime
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta
from collections import defaultdict

from django.db.models import Count

from qsstats import QuerySetStats
from qsstats.utils import get_bounds

from consumer.models import Consumer


def one_year_ago():
    """ Return date representing one year from current day. """
    return date.today() - timedelta(days=365)

def one_year_ago_plus():
    """ Return date that goes back one year, then back to the first day of
    that month.
    """
    last_year = one_year_ago()
    return date(last_year.year, last_year.month, 1)


class SiteConsumerStats(object):
    """ Generate totals and time-series for Consumers related to a site. """
    def __init__(self, site, queryset=None):
        self.site = site
        self.qs = queryset

    def get_queryset(self):
        """ Return a Consumer queryset for use in generating the time-series
        queryset.
        """
        return self.qs or Consumer.objects.filter(site=self.site)

    def get_timeseries_queryset(self):
        """ Return a time-series queryset. """
        qs = self.qs or self.get_queryset()
        return QuerySetStats(qs, 'consumer_create_datetime')

    def get_series(self, stype):
        """ Return the stype choice with underscores
        Ex: last-12-months ---> last_12_months
        """
        method = getattr(self, stype.replace('-', '_'))
        return method

    def __getattr__(self, value):
        self.cfg = {
            'last_12_months': {
                'total-since': one_year_ago(),
                'interval': 'days'},
            'last_30_days': {
                'total-since': date.today() - timedelta(days=30),
                'interval': 'days'}} \
            .get(value, {
                'total-since': self.site.launch_date,
                'interval': 'days'})

        tsqs = self.get_timeseries_queryset()
        return self.filter_series(tsqs,
                {'total': tsqs.after(self.cfg['total-since']),
                'series': self._fast_time_series(self.cfg['total-since'],
                    date.today(),
                    interval=self.cfg['interval'])})

    @staticmethod
    def filter_series(tsqs, series_data):
        """ Subclasses can override this for additional processing"""
        # Get the total as of the first day.
        total = tsqs.until(series_data['series'][0][0])
        months = defaultdict(int)
        month_series = []
        for day, signups  in series_data['series']:
            k = (day.year, day.month)
            months[k] += signups
            total += signups
            month_series.append((day, total))

        series_data['series'] = month_series
        return series_data

    def _fast_time_series(self, start, end=None, interval='days'):
        """ Aggregate over time intervals using just 1 sql query. """
        end = end or date.today()
        aggregate = Count('id')
        date_field = 'consumer_create_datetime'

        start = get_bounds(start, interval.rstrip('s'))[0]
        end = get_bounds(end, interval.rstrip('s'))[1]
        interval_sql = "%s::date" % date_field

        kwargs = {'%s__range' % date_field: (start, end)}
        aggregate_data = (self.get_queryset()
            .extra(select={'d': interval_sql})
            .filter(**kwargs).values('d')
            .annotate(agg=aggregate))

        data = dict((datetime.datetime(item['d'].year,
                                       item['d'].month,
                                       item['d'].day),
                    item['agg']) for item in aggregate_data)

        stat_list = []
        date_ = start
        while date_ < end:
            value = data.get(date_, 0)
            stat_list.append((date_, value,))
            date_ += relativedelta(**{interval: 1})
        return stat_list
