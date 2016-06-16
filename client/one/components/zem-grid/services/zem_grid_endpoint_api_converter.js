/* globals oneApp */
'use strict';

oneApp.factory('zemGridEndpointApiConverter', [function () {

    return {
        convertFromApi: convertFromApi,
        convertToApi: convertToApi,
    };

    function convertFromApi (config, breakdown, metaData) {
        breakdown.breakdownId = breakdown.breakdown_id;
        delete breakdown.breakdown_id;
        breakdown.level = config.level;
        breakdown.rows = breakdown.rows.map(function (row) {
            return {
                stats: convertStatsFromApi(row, metaData),
                breakdownId: row.breakdown_id,
                archived: row.archived,
            };
        });
        breakdown.totals = convertStatsFromApi(breakdown.totals, metaData);
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
        metaData.columns.forEach(function (column) {
            if (row[column.field]) {
                convertedStats[column.field] = convertField(row[column.field], column.type);
            }
        });
        convertedStats = setEditableFields(convertedStats, row.editable_fields);
        return convertedStats;
    }

    function convertField (value, type) {
        // TODO: On CAMPAIGN_AD_GROUPS level stateText is dynamically calculated based on state and row.archived. It
        // can't be converted from api, because no stateText field is returned from server.
        switch (type) {
        // TODO: convertBreakdownNameField (include name, id, url, etc.)
        // TODO: convertInternalLinkField
        // TODO: convertExternalLinkField
        // TODO: convertThumbnailField
        // TODO: convertSubmissionStatusField
        // TODO: convertPerformanceIndicatorField
        // TODO: convertTextWithPopupField
        default: return convertValueToDefaultObject(value);
        }
    }

    function setEditableFields (stats, editableFields) {
        if (!editableFields) {
            return stats;
        }
        Object.keys(editableFields).forEach(function (field) {
            if (stats[field]) {
                stats[field].isEditable = editableFields[field].enabled;
                stats[field].editMessage = editableFields[field].message;
            }
        });
        return stats;
    }

    function convertValueToDefaultObject (value) {
        return {
            value: value,
        };
    }
}]);
