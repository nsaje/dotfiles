/* globals oneApp */
/* eslint-disable camelcase*/
'use strict';

oneApp.factory('zemGridEndpointApiConverter', ['zemGridConstants', 'zemGridEndpointColumns', function (zemGridConstants, zemGridEndpointColumns) { // eslint-disable-line max-len

    return {
        convertBreakdownFromApi: convertBreakdownFromApi,
        convertConfigToApi: convertConfigToApi,
        convertField: convertField,
    };

    function convertBreakdownFromApi (config, breakdown, metaData) {
        var convertedBreakdown = {
            breakdownId: breakdown.breakdown_id,
            level: config.level,
            pagination: breakdown.pagination,
        };

        if (breakdown.campaign_goals) {
            convertedBreakdown.campaignGoals = breakdown.campaign_goals;
        }
        if (breakdown.conversion_goals) {
            convertedBreakdown.conversionGoals = breakdown.conversion_goals;
        }
        if (breakdown.enabling_autopilot_sources_allowed) {
            convertedBreakdown.enablingAutopilotSourcesAllowed = breakdown.enabling_autopilot_sources_allowed;
        }
        if (breakdown.ad_group_autopilot_state) {
            convertedBreakdown.adGroupAutopilotState = breakdown.ad_group_autopilot_state;
        }
        if (breakdown.batches) {
            convertedBreakdown.batches = breakdown.batches;
        }

        convertedBreakdown.totals = convertStatsFromApi(breakdown.totals, metaData);
        convertedBreakdown.rows = breakdown.rows.map(function (row) {
            return {
                stats: convertStatsFromApi(row, metaData),
                breakdownId: row.breakdown_id,
                archived: row.archived,
                supplyDashDisabledMessage: row.supply_dash_disabled_message,
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
            convertedStats[column.field] = convertField(row[column.field], column.type);
        });
        convertedStats = setLinkFields(
            convertedStats, row.url, row.redirector_url, row.title, row.supply_dash_disabled_message
        );
        convertedStats = setEditableFields(convertedStats, row.editable_fields);
        convertedStats = setGoalStatuses(convertedStats, row.styles);
        return convertedStats;
    }

    function convertField (value, type) {
        switch (type) {
        // TODO: convertThumbnailField
        // TODO: convertTextWithPopupField
        case zemGridConstants.gridColumnTypes.PERFORMANCE_INDICATOR: return value;
        case zemGridConstants.gridColumnTypes.SUBMISSION_STATUS: return value;
        case zemGridConstants.gridColumnTypes.VISIBLE_LINK: return convertUrlValue(value);
        case zemGridConstants.gridColumnTypes.ICON_LINK: return convertUrlValue(value);
        default: return convertValueToDefaultObject(value);
        }
    }

    function setLinkFields (stats, url, redirectorUrl, title, supplyDashDisabledMessage) {
        if (url !== undefined) {
            stats.urlLink = {
                text: url !== '' ? url : 'N/A',
                url: url !== '' ? url : null,
            };

            stats.titleLink = {
                text: title,
                url: url !== '' ? url : null,
                redirectorUrl: redirectorUrl !== '' ? redirectorUrl : null,
            };
        }

        return stats;
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

    function setGoalStatuses (stats, goalStatuses) {
        if (!goalStatuses) {
            return stats;
        }
        Object.keys(goalStatuses).forEach(function (field) {
            if (stats[field] !== undefined) {
                stats[field].goalStatus = goalStatuses[field];
            }
        });
        return stats;
    }

    function convertUrlValue (value) {
        return {
            url: value,
        };
    }

    function convertValueToDefaultObject (value) {
        return {
            value: value,
        };
    }
}]);
