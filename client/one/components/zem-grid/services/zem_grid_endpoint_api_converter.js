/* globals oneApp */
'use strict';

oneApp.factory('zemGridEndpointApiConverter', [function () {

    return {
        convertFromApi: convertFromApi,
        convertToApi: convertToApi,
    };

    function convertFromApi (config, breakdown, metaData) {
        breakdown.level = config.level;
        breakdown.breakdownId = breakdown.breakdown_id;
        breakdown.rows = breakdown.rows.map(function (row) {
            row.breakdownName = row.breakdown_name;
            return {
                stats: convertStatsFromApi(row, metaData),
                breakdownId: row.breakdown_id,
            };
        });
    }

    function convertToApi (config) {
        config.breakdown_page = config.breakdownPage; // eslint-disable-line camelcase
        config.start_date = config.startDate.format('YYYY-MM-DD'); // eslint-disable-line camelcase
        config.end_date = config.endDate.format('YYYY-MM-DD'); // eslint-disable-line camelcase
        delete config.breakdownPage;
        delete config.breakdown;
        return config;
    }

    function convertStatsFromApi (row, metaData) {
        var convertedStats = {};
        Object.keys(row).forEach(function (field) {
            convertedStats[field] = convertField(field, row, metaData);
        });
        return convertedStats;
    }

    function convertField (field, row, metaData) {
        var value = row[field];
        // TODO: Move column definitions to a separate service and use it to generate mocked data and to convert data
        // from api correctly.
        // columnDefinitions[field]['type'] = 'curreny/number/submissionStatus/...'
        // Based on this convert api data.
        var type;
        metaData.columns.forEach(function (column) {
            if (column.field === field) {
                type = column.type;
            }
        });
        switch (type) {
        case 'number': return convertNumberField(value);
        case 'percent': return convertPercentField(value);
        case 'currency': return convertCurrencyField(value);
        case 'seconds': return convertSecondsField(value);
        case 'datetime': return convertDatetimeField(value);
        case 'status': return convertStatusField(value, row);
        }
        return value;
    }

    function convertNumberField (value) {
        return {
            value: value,
        };
    }

    function convertPercentField (value) {
        return {
            value: value,
        };
    }

    function convertCurrencyField (value) {
        return {
            value: value,
        };
    }

    function convertSecondsField (value) {
        return {
            value: value,
        };
    }

    function convertDatetimeField (value) {
        return {
            value: value,
        };
    }

    function convertStatusField (value, row) {
        if (row.archived) {
            return 'Archived';
        } else if (value === '1') { // TODO: Use appropriate constant
            return 'Active';
        }
        return 'Paused';
    }
}]);
