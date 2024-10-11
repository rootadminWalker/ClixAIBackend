from datetime import datetime, time, timedelta, date


def get_closest_event_start_date(event_weekday: int, semester_start_date: datetime) -> datetime:
    """
    Get closest event start date from the semester start date
    :param event_weekday: 0, 1, 2, ..., 6
    :param semester_start_date: datetime.datetime
    :return: datetime.datetime
    """
    for i in range(7):
        if (n := semester_start_date + timedelta(days=i)).weekday() == event_weekday:
            return n


def str_weekday_to_idx(weekday: str):
    """
    Convert string weekday to idx
    :param weekday: Monday, Tuesday, .... Sunday, no mapper upper or lower cases
    :return: 0, 1, 2, ..., 6
    """
    return ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'].index(weekday.lower())


def str_date_to_datetime(str_date: str) -> date:
    """
    Convert string date to datetime.date format
    :param str_date: YYYY-MM-DD
    :return: datetime.datetime
    """
    return (datetime.strptime(str_date, '%Y-%m-%d')).date()


def milliseconds_to_time(milliseconds: int) -> time:
    return datetime.strptime(str(timedelta(milliseconds=milliseconds)), "%H:%M:%S").time()
