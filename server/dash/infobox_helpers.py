import datetime


def calculate_flight_time(start_date, end_date):
    end_date = end_date
    if end_date is not None:
        end_date_str = end_date.strftime('%m/%d')
    else:
        end_date_str = ''

    flight_time = "{start_date} - {end_date}".format(
        start_date=start_date.strftime('%m/%d'),
        end_date=end_date_str,
    )
    today = datetime.datetime.today().date()
    if not end_date:
        flight_time_left_days = None
    elif today > end_date:
        flight_time_left_days = 0
    else:
        flight_time_left_days = (end_date - today).days + 1
    return flight_time, flight_time_left_days
