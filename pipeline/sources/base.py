class SkipSource(Exception):
    """Raised by a source that cannot run in this environment (e.g. no API key). The run is logged as skipped."""
