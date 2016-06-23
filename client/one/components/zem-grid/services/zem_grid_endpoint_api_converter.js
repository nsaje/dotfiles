/* globals oneApp */
/* eslint-disable camelcase*/
'use strict';

oneApp.factory('zemGridEndpointApiConverter', [function () {

    return {
        convertBreakdownFromApi: convertBreakdownFromApi,
        convertConfigToApi: convertConfigToApi,
    };

    function convertBreakdownFromApi (config, breakdown, metaData) {
        var convertedBreakdown = {
            breakdownId: breakdown.breakdown_id,
            level: config.level,
            pagination: breakdown.pagination,
            totals: convertStatsFromApi(breakdown.totals, metaData),
        };
        convertedBreakdown.rows = breakdown.rows.map(function (row) {
            return {
                stats: convertStatsFromApi(row, metaData),
                breakdownId: row.breakdown_id,
                archived: row.archived,
            };
        });
        return convertedBreakdown;
    }

    function convertConfigToApi (config) {
        return {
            breakdown_page: config.breakdownPage,
            start_date: config.startDate.format('YYYY-MM-DD'),
            end_date: config.endDate.format('YYYY-MM-DD'),
            show_archived: config.showArchived,
            show_blacklisted_publishers: config.showBlacklistedPublishers,
            filtered_sources: config.filteredSources,
            level: config.level,
            limit: config.limit,
            offset: config.offset,
            order: config.order,
        };
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
        // TODO: convertExternalLinkField
        // TODO: convertThumbnailField
        // TODO: convertSubmissionStatusField
        // TODO: convertTextWithPopupField
        case 'performanceIndicator': return value;
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
