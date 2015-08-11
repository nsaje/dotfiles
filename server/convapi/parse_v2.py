class CsvReport(IReport):

    REQUIRED_FIELDS = [
        'Sessions',
        '% New Sessions',
        'New Users',
        'Bounce Rate',
        'Pages / Session',
        'Avg. Session Duration',
    ]

    def __init__(self, raw, report_log):
        pass
