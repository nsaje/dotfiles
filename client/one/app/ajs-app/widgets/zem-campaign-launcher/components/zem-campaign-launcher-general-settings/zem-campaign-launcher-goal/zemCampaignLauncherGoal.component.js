require('./zemCampaignLauncherGoal.component.less');
var constantsHelpers = require('../../../../../../shared/helpers/constants.helpers');
var currencyHelpers = require('../../../../../../shared/helpers/currency.helpers');
var campaignGoalsHelpers = require('../../../../../../features/entity-manager/helpers/campaign-goals.helpers');

angular.module('one.widgets').component('zemCampaignLauncherGoal', {
    bindings: {
        stateService: '<',
        account: '<',
    },
    template: require('./zemCampaignLauncherGoal.component.html'),
    controller: function(
        $filter,
        zemConversionPixelsEndpoint,
        zemNavigationNewService
    ) {
        var $ctrl = this;

        $ctrl.updateCampaignGoal = updateCampaignGoal;

        function getAvailableGoals() {
            var campaignType = parseInt(
                constantsHelpers.convertFromName(
                    $ctrl.state.fields.type,
                    constants.campaignTypes
                )
            );
            var availableGoals = campaignGoalsHelpers.getAvailableGoals(
                options.campaignGoalKPIs,
                [],
                campaignType,
                false
            );
            var activeAccount = zemNavigationNewService.getActiveAccount();
            return mapAvailableGoalsToCurrencySymbol(
                availableGoals,
                currencyHelpers.getCurrencySymbol(
                    activeAccount && activeAccount.data
                        ? activeAccount.data.currency
                        : null
                )
            );
        }

        function mapAvailableGoalsToCurrencySymbol(
            availableGoals,
            currencySymbol
        ) {
            return availableGoals.map(function(goal) {
                if (goal.isCurrency) {
                    goal.unit = currencySymbol;
                }
                return goal;
            });
        }

        $ctrl.$onInit = function() {
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.availableGoals = getAvailableGoals();
            $ctrl.goalsDefaults = $ctrl.stateService.getCampaignGoalsDefaults();

            $ctrl.pixels = {};

            if ($ctrl.state.fields.campaignGoal) {
                $ctrl.newCampaignGoal = angular.copy(
                    $ctrl.state.fields.campaignGoal
                );
            } else {
                $ctrl.newCampaignGoal = {primary: true};
            }

            $ctrl.pixels.loading = true;
            zemConversionPixelsEndpoint
                .list($ctrl.account.id)
                .then(function(data) {
                    var availablePixels = data.rows.filter(function(pixel) {
                        return !pixel.archived;
                    });
                    $ctrl.pixels.list = getPixelsWithConversionWindows(
                        availablePixels
                    );
                    $ctrl.pixels.loading = false;
                });
        };

        function updateCampaignGoal(goal) {
            $ctrl.state.fields.campaignGoal = goal;
            $ctrl.stateService.validateFields();
        }

        function getPixelsWithConversionWindows(pixels) {
            pixels.forEach(function(pixel) {
                pixel.conversionWindows = options.conversionWindows;
            });
            return pixels;
        }
    },
});
