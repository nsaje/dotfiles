var currencyHelpers = require('../../../../../shared/helpers/currency.helpers');
var clone = require('clone');

angular.module('one.widgets').component('zemInfoboxRealtimestats', {
    bindings: {
        entity: '<',
    },
    template: require('./zemInfoboxRealtimestats.component.html'),
    controller: function(zemRealtimestatsService, $interval, $timeout) {
        // eslint-disable-line max-len
        var $ctrl = this;

        var BIDDING_TYPE_CPC = 1;

        var SPEND_ROW_DEFAULTS = {
            name: "Today's spend:",
            warning:
                "Today's spend is calculated in real-time and represents the amount of money spent on media and data costs today. Today's spend does not include fees that might apply. The final amount might be different due to post-processing.", // eslint-disable-line max-len
        };

        var AVERAGE_ROW_DEFAULTS = {
            name: "Today's avg. {biddingType}:",
            warning:
                'Today’s avg. {biddingType} displays Autopilot’s current bid and is updated in real-time.',
        };

        $ctrl.realtimeRows = [];

        var pollInterval;

        $ctrl.$onChanges = function(changes) {
            if (changes.entity) {
                if (pollInterval) $interval.cancel(pollInterval);
                if (
                    $ctrl.entity &&
                    $ctrl.entity.type === constants.entityType.AD_GROUP
                ) {
                    updateAdGroupStats();
                    pollInterval = $interval(updateAdGroupStats, 10000);
                } else {
                    $ctrl.realtimeRows = [];
                    stopPolling();
                }
            }
        };

        $ctrl.$onDestroy = function() {
            stopPolling();
        };

        function stopPolling() {
            if (pollInterval) {
                $interval.cancel(pollInterval);
            }
        }

        function formatSpendRow(spendBySource) {
            var totalSpend = getTotalSpend(spendBySource);

            var rowDetails = spendBySource
                .map(function(stat) {
                    return stat.source + ': ' + formatSpend(stat.spend, 2);
                })
                .join('<br />');

            var oldValue = $ctrl.spendRow ? $ctrl.spendRow.value : null;
            return formatRow(
                oldValue,
                SPEND_ROW_DEFAULTS,
                [],
                formatSpend(totalSpend, 2),
                rowDetails
            );
        }

        function formatAverageRow(todaysAvgSpend) {
            var biddingType =
                $ctrl.entity.data.bidding_type === BIDDING_TYPE_CPC
                    ? 'CPC'
                    : 'CPM';

            var oldValue = $ctrl.averageRow ? $ctrl.averageRow.value : null;
            return formatRow(
                oldValue,
                AVERAGE_ROW_DEFAULTS,
                [['{biddingType}', biddingType]],
                formatSpend(todaysAvgSpend, 3),
                undefined
            );
        }

        function formatRow(
            oldValue,
            defaults,
            textReplacements,
            newValue,
            detailsContent
        ) {
            var row = clone(defaults);

            (textReplacements || []).forEach(function(textReplacement) {
                row.name = row.name.replace(
                    textReplacement[0],
                    textReplacement[1]
                );
                row.warning = row.warning.replace(
                    textReplacement[0],
                    textReplacement[1]
                );
            });
            row.value = newValue;
            row.detailsContent = detailsContent;

            if (newValue !== oldValue) {
                row.class = 'zem-infobox-data-row--update';
                $timeout(function() {
                    row.class = '';
                }, 1000);
            }

            return row;
        }

        function updateAdGroupStats() {
            zemRealtimestatsService
                .getAdGroupSourcesStats($ctrl.entity.id)
                .then(function(sourceStats) {
                    $ctrl.realtimeRows = [
                        formatSpendRow(sourceStats.spend),
                        formatAverageRow(getAdGroupAverageSpend(sourceStats)),
                    ];
                });
        }

        function formatSpend(spend, fractionSize) {
            var account = $ctrl.entity.parent.parent;
            var currency =
                account && account.data ? account.data.currency : null;
            return currencyHelpers.getValueInCurrency(
                spend,
                currency,
                fractionSize
            );
        }

        function getAdGroupAverageSpend(sourceStats) {
            var spend = getTotalSpend(sourceStats.spend);

            if ($ctrl.entity.data.bidding_type === BIDDING_TYPE_CPC) {
                var clicks = sourceStats.clicks || 0;
                return clicks === 0 ? 0 : spend / clicks;
            }
            // Else if CPM:
            var milleImpressions = (sourceStats.impressions || 0) / 1000;
            return milleImpressions === 0 ? 0 : spend / milleImpressions;
        }

        function getTotalSpend(spendBySource) {
            return spendBySource.reduce(function(sum, current) {
                return sum + parseFloat(current.spend);
            }, 0);
        }
    },
});
