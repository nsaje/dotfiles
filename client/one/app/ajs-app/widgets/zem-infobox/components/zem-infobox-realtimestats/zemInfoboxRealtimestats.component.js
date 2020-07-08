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

        var spendRowDefaults = {
            name: "Today's spend:",
            warning:
                "Today's spend is calculated in real-time and represents the amount of money spent on media and data costs today. Today's spend does not include fees that might apply. The final amount might be different due to post-processing.", // eslint-disable-line max-len
        };

        $ctrl.spendRow = null;

        var pollInterval;

        $ctrl.$onChanges = function(changes) {
            if (changes.entity) {
                if (pollInterval) $interval.cancel(pollInterval);
                if (
                    $ctrl.entity &&
                    $ctrl.entity.type === constants.entityType.AD_GROUP
                ) {
                    $ctrl.spendRow = clone(spendRowDefaults);
                    update();
                    pollInterval = $interval(update, 10000);
                } else {
                    $ctrl.spendRow = null;
                }
            }
        };

        $ctrl.$onDestroy = function() {
            if (pollInterval) $interval.cancel(pollInterval);
        };

        function update() {
            zemRealtimestatsService
                .getAdGroupSourcesStats($ctrl.entity.id)
                .then(function(sourceStats) {
                    var oldValue = clone($ctrl.spendRow.value);

                    $ctrl.spendRow.value = formatSpend(
                        sourceStats.reduce(function(sum, stat) {
                            return sum + parseFloat(stat.spend);
                        }, 0)
                    );
                    $ctrl.spendRow.detailsContent = sourceStats
                        .map(function(stat) {
                            return stat.source + ': ' + formatSpend(stat.spend);
                        })
                        .join('<br />');

                    if (oldValue !== $ctrl.spendRow.value) {
                        $ctrl.spendRow.class = 'zem-infobox-data-row--update';
                        $timeout(function() {
                            $ctrl.spendRow.class = '';
                        }, 1000);
                    }
                });
        }

        function formatSpend(spend) {
            // adgroup.campaign.account
            var account = $ctrl.entity.parent.parent;
            var currency =
                account && account.data ? account.data.currency : null;
            return currencyHelpers.getValueInCurrency(spend, currency, 4);
        }
    },
});
