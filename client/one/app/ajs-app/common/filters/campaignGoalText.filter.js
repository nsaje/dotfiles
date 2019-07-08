var currencyHelpers = require('../../../shared/helpers/currency.helpers');

angular
    .module('one.common')
    .filter('campaignGoalText', function($filter, zemNavigationNewService) {
        // eslint-disable-line max-len
        return function(goal) {
            if (!goal) {
                return '';
            }

            if (
                [
                    constants.campaignGoalKPI.CPA,
                    constants.campaignGoalKPI.CPC,
                    constants.campaignGoalKPI.CPM,
                    constants.campaignGoalKPI.CPV,
                    constants.campaignGoalKPI.CP_NON_BOUNCED_VISIT,
                    constants.campaignGoalKPI.CP_NEW_VISITOR,
                    constants.campaignGoalKPI.CP_PAGE_VIEW,
                    constants.campaignGoalKPI.CPCV,
                ].indexOf(goal.type) > -1
            ) {
                var fractionSize = 2;
                if (goal.type === constants.campaignGoalKPI.CPC) {
                    fractionSize = 3;
                }
                var activeAccount = zemNavigationNewService.getActiveAccount();
                var currency =
                    activeAccount && activeAccount.data
                        ? activeAccount.data.currency
                        : null;
                var formattedValue = currencyHelpers.getValueInCurrency(
                    goal.value,
                    currency,
                    fractionSize
                );
                return (
                    formattedValue +
                    ' ' +
                    constants.campaignGoalValueText[goal.type]
                );
            } else if (
                [
                    constants.campaignGoalKPI.TIME_ON_SITE,
                    constants.campaignGoalKPI.MAX_BOUNCE_RATE,
                    constants.campaignGoalKPI.PAGES_PER_SESSION,
                    constants.campaignGoalKPI.NEW_UNIQUE_VISITORS,
                ].indexOf(goal.type) > -1
            ) {
                return (
                    $filter('number')(goal.value, 2) +
                    ' ' +
                    constants.campaignGoalValueText[goal.type]
                );
            }
        };
    });
