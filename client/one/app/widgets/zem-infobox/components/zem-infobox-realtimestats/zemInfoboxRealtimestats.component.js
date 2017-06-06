angular.module('one.widgets').component('zemInfoboxRealtimestats', {
    bindings: {
    },
    templateUrl: '/app/widgets/zem-infobox/components/zem-infobox-realtimestats/zemInfoboxRealtimestats.component.html',
    controller: function (zemNavigationNewService, zemRealtimestatsService, $filter, $interval) {
        var $ctrl = this;

        var spendRow = {
            name: 'Today\'s spend:',
            warning: 'Today\'s spend is calculated in real-time and represents the amount of money spent on media and data costs today. Today\'s spend does not include fees that might apply. The final amount might be different due to post-processing. Outbrain, Yahoo and Facebook today\'s spend is not available.',  // eslint-disable-line max-len
        };

        $ctrl.spendRow = null;

        var pollInterval, entity;
        $ctrl.$onInit = function () {
            entity = zemNavigationNewService.getActiveEntity();
            if (entity && entity.type === constants.entityType.AD_GROUP) {
                update();
                pollInterval = $interval(update, 10000);
                $ctrl.spendRow = spendRow;
            } else {
                $ctrl.spendRow = null;
            }
        };

        $ctrl.$onDestroy = function () {
            if (pollInterval) {
                $interval.cancel(pollInterval);
            }
        };

        function update () {
            zemRealtimestatsService.getAdGroupSourcesStats(entity.id).then(function (sourceStats) {
                spendRow.value = formatSpend(sourceStats.reduce(function (sum, stat) {
                    return sum + stat.spend;
                }, 0));
                spendRow.detailsContent = sourceStats.map(function (stat) {
                    return stat.source + ': ' + formatSpend(stat.spend);
                }).join('<br />');
            });
        }

        function formatSpend (spend) {
            return $filter('decimalCurrency')(spend, '$', 4);
        }
    },
});
