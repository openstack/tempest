import datetime


#TODO(bcwaldon): expand this to support more iso-compliant formats
ISO_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def load_isotime(time_str):
    """Convert formatted time stjring to a datetime object."""
    return datetime.datetime.strptime(time_str, ISO_TIME_FORMAT)


def dump_isotime(datetime_obj):
    """Format a datetime object as an iso-8601 string."""
    return datetime_obj.strftime(ISO_TIME_FORMAT)
