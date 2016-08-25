/* globals angular, oneApp, constants */
/* eslint-disable camelcase*/
'use strict';

oneApp.factory('zemGridEndpointApiConverter', ['zemGridConstants', 'zemGridEndpointColumns', function (zemGridConstants, zemGridEndpointColumns) { // eslint-disable-line max-len

    return {
        convertBreakdownFromApi: convertBreakdownFromApi,
        convertConfigToApi: convertConfigToApi,
        convertSettingsToApi: convertSettingsToApi,
    };

    function convertBreakdownFromApi (config, breakdown, metaData) {
        var convertedBreakdown = {
            breakdownId: breakdown.breakdown_id,
            level: config.level,
            pagination: breakdown.pagination,
        };

        // TODO: find better solution for optional fields (and camelcase converting)
        if (breakdown.campaign_goals) {
            convertedBreakdown.campaignGoals = breakdown.campaign_goals;
        }
        if (breakdown.conversion_goals) {
            convertedBreakdown.conversionGoals = breakdown.conversion_goals;
        }
        if (breakdown.pixels) {
            convertedBreakdown.pixels = breakdown.pixels;
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
        if (breakdown.notification) {
            convertedBreakdown.notification = breakdown.notification;
        }

        zemGridEndpointColumns.setDynamicColumns(
            metaData.columns,
            metaData.categories,
            breakdown.campaignGoals,
            breakdown.conversionGoals,
            breakdown.pixels
        );

        if (breakdown.totals) {
            convertedBreakdown.totals = convertStatsFromApi(breakdown.totals, metaData);
        }

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
            filtered_account_types: config.filteredAccountTypes,
            filtered_agencies: config.filteredAgencies,
            level: config.level,
            limit: config.limit,
            offset: config.offset,
            order: config.order,
        };
    }

    function convertSettingsToApi (settings) {
        var convertedSettings = {};
        Object.keys(settings).forEach(function (key) {
            switch (key) {
            case zemGridEndpointColumns.COLUMNS.bidCpcSetting.field:
                convertedSettings['cpc_cc'] = settings[key];
                break;
            case zemGridEndpointColumns.COLUMNS.dailyBudgetSetting.field:
                convertedSettings['daily_budget_cc'] = settings[key];
                break;
            default:
                convertedSettings[key] = settings[key];
            }
        });
        return convertedSettings;
    }

    function convertStatsFromApi (row, metaData) {
        var convertedStats = {};
        metaData.columns.forEach(function (column) {
            convertedStats[column.field] = convertField(row[column.field], column.type);
        });
        convertedStats = setUrlLinkField(convertedStats, row.url);
        convertedStats = setBreakdownField(convertedStats, metaData, row.url, row.redirector_url, row.title);
        convertedStats = setEditableFields(convertedStats, row.editable_fields);
        convertedStats = setGoalStatuses(convertedStats, row.styles);
        return convertedStats;
    }

    function convertField (value, type) {
        switch (type) {
        case zemGridConstants.gridColumnTypes.PERFORMANCE_INDICATOR: return value;
        case zemGridConstants.gridColumnTypes.SUBMISSION_STATUS: return value;
        case zemGridConstants.gridColumnTypes.STATE_SELECTOR: return value;
        case zemGridConstants.gridColumnTypes.STATUS: return convertStatusValue(value);
        case zemGridConstants.gridColumnTypes.THUMBNAIL: return convertThumbnailValue(value);
        case zemGridConstants.gridColumnTypes.VISIBLE_LINK: return convertUrlValue(value);
        case zemGridConstants.gridColumnTypes.ICON_LINK: return convertUrlValue(value);
        default: return convertValueToDefaultObject(value);
        }
    }

    function setUrlLinkField (stats, url) {
        if (url !== undefined) {
            stats.urlLink = {
                text: url !== '' ? url : 'N/A',
                url: url !== '' ? url : null,
            };
        }
        return stats;
    }

    function setBreakdownField (stats, metaData, url, redirectorUrl, title) {
        if (metaData.breakdown === constants.breakdown.CONTENT_AD) {
            var titleLink = {
                text: title,
                url: url !== '' ? url : null,
                redirectorUrl: redirectorUrl !== '' ? redirectorUrl : null,
            };
            angular.extend(stats[zemGridEndpointColumns.COLUMNS.name.field], titleLink);
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

    function convertThumbnailValue (value) {
        if (value) {
            return {
                square: value.square || null,
                landscape: value.landscape || null,
            };
        }
    }

    function convertUrlValue (value) {
        return {
            url: value,
        };
    }

    function convertStatusValue (status) {
        if (status) {
            return {
                value: status.value,
                popoverMessage: status.popover_message,
                important: status.important,
            };
        }
    }

    function convertValueToDefaultObject (value) {
        return {
            value: value,
        };
    }
}]);
