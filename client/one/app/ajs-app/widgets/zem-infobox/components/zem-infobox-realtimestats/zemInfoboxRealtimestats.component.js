angular.module('one.widgets').component('zemInfoboxRealtimestats', {
    bindings: {
    },
    template: require('./zemInfoboxRealtimestats.component.html'),
    controller: function (zemNavigationNewService, zemRealtimestatsService, zemMulticurrencyService, $filter, $interval, $timeout) {
        var $ctrl = this;

        var spendRow = {
            name: 'Today\'s spend:',
            warning: 'Today\'s spend is calculated in real-time and represents the amount of money spent on media and data costs today. Today\'s spend does not include fees that might apply. The final amount might be different due to post-processing. Outbrain, Yahoo and Facebook today\'s spend is delayed by 15 minutes. Yahoo data is offset because of the time zone difference and will not be displayed for the first 3 hours of the day.',  // eslint-disable-line max-len
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
                var oldValue = spendRow.value;

                spendRow.value = formatSpend(sourceStats.reduce(function (sum, stat) {
                    return sum + parseFloat(stat.spend);
                }, 0));
                spendRow.detailsContent = sourceStats.map(function (stat) {
                    return stat.source + ': ' + formatSpend(stat.spend);
                }).join('<br />');

                if (oldValue !== spendRow.value) {
                    spendRow.class = 'zem-infobox-data-row--update';
                    $timeout(function () {
                        spendRow.class = '';
                    }, 1000);
                }
            });
        }

        function formatSpend (spend) {
            var currencySymbol = zemMulticurrencyService.getAppropriateCurrencySymbol(
                zemNavigationNewService.getActiveAccount(),
                ['zemauth.can_see_infobox_in_local_currency'],
            );
            return $filter('decimalCurrency')(spend, currencySymbol, 4);
        }
    },
});
