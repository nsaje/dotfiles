/* eslint-disable camelcase*/

var commonHelpers = require('../../../../../shared/helpers/common.helpers');

angular
    .module('one.widgets')
    .factory('zemGridEndpointApiConverter', function(
        zemGridConstants,
        zemGridEndpointColumns,
        zemUtils
    ) {
        // eslint-disable-line max-len
        var DELIVERY_BREAKDOWNS;

        return {
            convertBreakdownFromApi: convertBreakdownFromApi,
            convertConfigToApi: convertConfigToApi,
            convertSettingsToApi: convertSettingsToApi,
        };

        function convertBreakdownFromApi(
            config,
            breakdown,
            metaData,
            convertDiffAfterSave
        ) {
            var convertedBreakdown = zemUtils.convertToCamelCase(breakdown);
            convertedBreakdown.level = config.level;

            // Update DELIVERY_BREAKDOWNS list used in fields conversion
            if (metaData.breakdownGroups && metaData.breakdownGroups.delivery) {
                DELIVERY_BREAKDOWNS = (
                    metaData.breakdownGroups.delivery.breakdowns || []
                ).map(function(b) {
                    return b.query;
                });
            } else {
                DELIVERY_BREAKDOWNS = [];
            }

            if (config.level === 1 && !convertDiffAfterSave) {
                // set dynamic columns based on pixels, conversion goals and campaign goals from response
                // this has to be set before stats rows are converted since it adds new column definitions
                zemGridEndpointColumns.setDynamicColumns(
                    metaData.columns,
                    metaData.categories,
                    convertedBreakdown.campaignGoals,
                    convertedBreakdown.conversionGoals,
                    convertedBreakdown.pixels
                );
            }

            if (breakdown.totals) {
                convertedBreakdown.totals = convertStatsFromApi(
                    breakdown.totals,
                    metaData,
                    config
                );
            }

            convertedBreakdown.rows = breakdown.rows
                ? breakdown.rows.map(function(row) {
                      return {
                          stats: convertStatsFromApi(row, metaData, config),
                          group: row.group,
                          breakdownId: row.breakdown_id,
                          archived: row.archived,
                          supplyDashDisabledMessage:
                              row.supply_dash_disabled_message,
                          entity: getRowEntity(config, row.breakdown_id),
                      };
                  })
                : [];

            // Create groups for rows with special group property
            // Group breakdown contains rows defined in 'row.group.ids'
            createGroups(convertedBreakdown);

            return convertedBreakdown;
        }

        function createGroups(breakdown) {
            breakdown.rows
                .filter(function(row) {
                    return row.group;
                })
                .forEach(function(groupRow) {
                    createGroup(breakdown, groupRow);
                });
        }

        function createGroup(breakdown, groupRow) {
            var groupedRows = breakdown.rows.filter(function(row) {
                return groupRow.group.ids.indexOf(row.breakdownId) >= 0;
            });

            groupedRows.forEach(function(row) {
                var idx = breakdown.rows.indexOf(row);
                breakdown.rows.splice(idx, 1);
            });

            groupRow.breakdown = {
                breakdownId: groupRow.breakdownId,
                group: true,
                meta: {},
                level: 1,
                rows: groupedRows,
                pagination: {
                    complete: true,
                },
            };
        }

        function convertConfigToApi(config) {
            return {
                parents: config.breakdownParents,
                start_date: config.startDate.format('YYYY-MM-DD'),
                end_date: config.endDate.format('YYYY-MM-DD'),
                show_archived: config.showArchived,
                show_blacklisted_publishers: config.showBlacklistedPublishers,
                filtered_sources: config.filteredSources,
                filtered_account_types: config.filteredAccountTypes,
                filtered_businesses: config.filteredBusinesses,
                filtered_agencies: config.filteredAgencies,
                level: config.level,
                limit: config.limit,
                offset: config.offset,
                order: config.order,
            };
        }

        function convertSettingsToApi(settings) {
            var convertedSettings = {};
            Object.keys(settings).forEach(function(key) {
                switch (key) {
                    case zemGridEndpointColumns.COLUMNS.bidCpcSetting.field:
                        convertedSettings.cpc_cc = settings[key];
                        break;
                    case zemGridEndpointColumns.COLUMNS.bidCpmSetting.field:
                        convertedSettings.cpm = settings[key];
                        break;
                    case zemGridEndpointColumns
                        .COLUMNS.dailyBudgetSetting.field:
                        convertedSettings.daily_budget_cc = settings[key];
                        break;
                    default:
                        convertedSettings[key] = settings[key];
                }
            });
            return convertedSettings;
        }

        function convertStatsFromApi(row, metaData, config) {
            var convertedStats = {};
            metaData.columns.forEach(function(column) {
                convertedStats[column.field] = convertField(
                    config,
                    metaData,
                    column,
                    row[column.field]
                );
            });
            convertedStats = setUrlLinkField(convertedStats, row.url);
            convertedStats = setBreakdownField(
                convertedStats,
                metaData,
                row.url,
                row.redirector_url,
                row.title
            );
            convertedStats = setEditableFields(
                convertedStats,
                row.editable_fields
            );
            convertedStats = setGoalStatuses(convertedStats, row.styles);
            return convertedStats;
        }

        function convertField(config, metaData, column, value) {
            switch (column.type) {
                case zemGridConstants.gridColumnTypes.PERFORMANCE_INDICATOR:
                    return value;
                case zemGridConstants.gridColumnTypes.SUBMISSION_STATUS:
                    return value;
                case zemGridConstants.gridColumnTypes.STATE_SELECTOR:
                    return value;
                case zemGridConstants.gridColumnTypes.STATUS:
                    return convertStatusValue(value);
                case zemGridConstants.gridColumnTypes.THUMBNAIL:
                    return convertThumbnailValue(value);
                case zemGridConstants.gridColumnTypes.VISIBLE_LINK:
                    return convertUrlValue(value);
                case zemGridConstants.gridColumnTypes.ICON_LINK:
                    return convertUrlValue(value);
                case zemGridConstants.gridColumnTypes.BID_MODIFIER_FIELD:
                    return convertBidModifierValue(
                        config,
                        metaData,
                        column,
                        value
                    );
                default:
                    return convertValueToDefaultObject(
                        config,
                        metaData,
                        column,
                        value
                    );
            }
        }

        function setUrlLinkField(stats, url) {
            if (url !== undefined) {
                stats.urlLink = {
                    text: url !== '' ? url : 'N/A',
                    url: url !== '' ? url : null,
                };
            }
            return stats;
        }

        function setBreakdownField(stats, metaData, url, redirectorUrl, title) {
            var titleLink = {
                text: title,
                url: url !== '' ? url : null,
                redirectorUrl: redirectorUrl !== '' ? redirectorUrl : null,
            };
            angular.extend(
                stats[zemGridEndpointColumns.COLUMNS.name.field],
                titleLink
            );
            return stats;
        }

        function setEditableFields(stats, editableFields) {
            if (!editableFields) {
                return stats;
            }
            Object.keys(editableFields).forEach(function(field) {
                if (stats[field]) {
                    stats[field].isEditable = editableFields[field].enabled;
                    stats[field].editMessage = editableFields[field].message;
                }
            });
            return stats;
        }

        function setGoalStatuses(stats, goalStatuses) {
            if (!goalStatuses) {
                return stats;
            }
            Object.keys(goalStatuses).forEach(function(field) {
                if (stats[field] !== undefined) {
                    stats[field].goalStatus = goalStatuses[field];
                }
            });
            return stats;
        }

        function convertThumbnailValue(value) {
            if (value) {
                return {
                    square: value.square || null,
                    landscape: value.landscape || null,
                    icon: value.icon || null,
                    image: value.image || null,
                    ad_tag: value.ad_tag || null,
                };
            }
        }

        function convertUrlValue(value) {
            return {
                url: value,
            };
        }

        function convertBidModifierValue(config, metaData, column, value) {
            if (value) {
                var convertedValue = {};
                convertedValue.id = value.id;
                convertedValue.type = value.type;
                convertedValue.sourceSlug = value.source_slug;
                convertedValue.target = value.target
                    ? value.target.toString()
                    : null;
                convertedValue.bidMin = value.bid_min
                    ? parseFloat(value.bid_min).toFixed(2)
                    : null;
                convertedValue.bidMax = value.bid_max
                    ? parseFloat(value.bid_max).toFixed(2)
                    : null;
                convertedValue.modifier = value.modifier;

                return convertValueToDefaultObject(
                    config,
                    metaData,
                    column,
                    convertedValue
                );
            }
        }

        function convertStatusValue(status) {
            if (status) {
                return {
                    value: status.value,
                    popoverMessage: status.popover_message,
                    important: status.important,
                };
            }
        }

        function convertValueToDefaultObject(config, metaData, column, value) {
            var convertedObject = {value: value};
            var popoverMessage = getPopoverMessage(
                config,
                metaData,
                column,
                value
            );
            if (popoverMessage) {
                convertedObject.popoverMessage = popoverMessage;
            }
            return convertedObject;
        }

        function getPopoverMessage(config, metaData, column, value) {
            if (
                (value === undefined || value === null) &&
                zemGridEndpointColumns.isAudienceMetricColumn(column)
            ) {
                var rowBreakdown = config.breakdown[config.level - 1];
                if (DELIVERY_BREAKDOWNS.indexOf(rowBreakdown.query) !== -1) {
                    return 'Due to technical limitations breakdowns for on-site engagement metrics are not available.';
                }
            } else if (
                column.type === zemGridConstants.gridColumnTypes.BREAKDOWN &&
                commonHelpers.isDefined(value) &&
                value.toLowerCase() === 'not reported'
            ) {
                return 'Due to technical and supply source limitations we are not able to report breakdowns for all your data.'; // eslint-disable-line max-len
            }
        }

        function getRowEntity(config, breakdownId) {
            var type;
            var breakdown = config.breakdown[config.level - 1].query;

            switch (breakdown) {
                case constants.breakdown.ACCOUNT:
                    type = constants.entityType.ACCOUNT;
                    break;
                case constants.breakdown.CAMPAIGN:
                    type = constants.entityType.CAMPAIGN;
                    break;
                case constants.breakdown.AD_GROUP:
                    type = constants.entityType.AD_GROUP;
                    break;
                case constants.breakdown.CONTENT_AD:
                    type = constants.entityType.CONTENT_AD;
                    break;
                default:
                    return null;
            }

            var id =
                typeof breakdownId === 'string'
                    ? breakdownId.split('||')[config.level - 1]
                    : breakdownId;

            return {
                type: type,
                id: parseInt(id),
            };
        }
    });
