angular
    .module('one.common')
    .service('zemHeaderDateRangePickerService', function() {
        this.getPredefinedRanges = getPredefinedRanges;

        function getPredefinedRanges() {
            var ranges = {};

            ranges.Yesterday = [
                moment()
                    .subtract(1, 'days')
                    .startOf('day'),
                moment()
                    .subtract(1, 'days')
                    .endOf('day'),
            ]; // eslint-disable-line dot-notation, max-len
            ranges['Last 7 Days'] = [
                moment().subtract(7, 'days'),
                moment().subtract(1, 'days'),
            ];
            ranges['Last 30 Days'] = [
                moment().subtract(30, 'days'),
                moment().subtract(1, 'days'),
            ];
            ranges['This Month'] = [
                moment().startOf('month'),
                moment().endOf('month'),
            ];
            ranges['Last Month'] = [
                moment()
                    .subtract(1, 'month')
                    .startOf('month'),
                moment()
                    .subtract(1, 'month')
                    .endOf('month'),
            ]; // eslint-disable-line max-len
            ranges['Year to date'] = [
                moment().startOf('year'),
                moment().subtract(1, 'days'),
            ];

            return ranges;
        }
    });
