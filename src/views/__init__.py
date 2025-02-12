from fastapi.templating import Jinja2Templates
from collections import defaultdict
import datetime
import dateutil.parser

templates = Jinja2Templates(directory="templates")


_YEAR_THRESHOLD = 50  # Aggregate all date counts older than this year - _YEAR_THRESHOLD
_DATE_THRESHOLD = 0.975  # Ignore percentage of older dates during accumulation


def generate_date_histogram(date_counts):
    if not date_counts:
        return {}

    min_date_float = (
        datetime.datetime.now() - datetime.timedelta(days=_YEAR_THRESHOLD * 365)
    ).strftime("%Y-%m")

    histogram = defaultdict(lambda: 0)
    for date, count in date_counts.items():
        date_float = dateutil.parser.isoparse(date).strftime("%Y-%m")
        if date_float < min_date_float:
            histogram[min_date_float] += count
        else:
            histogram[date_float] += count

    min_date = sorted(histogram.keys())[0]
    max_date = datetime.datetime.now().strftime("%Y-%m")
    min_year, min_month = (int(x) for x in min_date.split("-"))
    max_year, max_month = (int(x) for x in max_date.split("-"))
    for year in range(min_year, max_year + 1):
        for i in range(12):
            i += 1
            if year == min_year and i < min_month:
                continue
            if year == max_year and i > max_month:
                continue
            year_month = f"{year}-{i:02}"
            if year_month not in histogram:
                histogram[year_month] = 0

    return histogram


def generate_cumulative_date_histogram(date_counts):
    if not date_counts:
        return {}

    histogram = defaultdict(lambda: 0)
    for date, count in date_counts.items():
        date_float = dateutil.parser.isoparse(date).strftime("%Y-%m")
        histogram[date_float] += count

    cumulative_date_counts = 0
    total_date_counts = sum(histogram.values())
    for date in sorted(histogram.keys(), reverse=True):
        cumulative_date_counts += histogram[date]
        if (
            cumulative_date_counts - histogram[date] > 0
            and cumulative_date_counts / total_date_counts > _DATE_THRESHOLD
        ):
            histogram.pop(date)

    cumulative_date_counts = 0
    min_date = sorted(histogram.keys())[0]
    max_date = datetime.datetime.now().strftime("%Y-%m")
    min_year, min_month = (int(x) for x in min_date.split("-"))
    max_year, max_month = (int(x) for x in max_date.split("-"))
    for year in range(min_year, max_year + 1):
        for i in range(12):
            i += 1
            if year == min_year and i < min_month:
                continue
            if year == max_year and i > max_month:
                continue
            year_month = f"{year}-{i:02}"
            if year_month in histogram:
                cumulative_date_counts += histogram[year_month]
            histogram[year_month] = cumulative_date_counts

    return histogram
