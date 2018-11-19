require('./zemCampaignLauncherGoal.component.less');
var constantsHelpers = require('../../../../../../shared/helpers/constants.helpers');

angular.module('one.widgets').component('zemCampaignLauncherGoal', {
    bindings: {
        stateService: '<',
        account: '<',
    },
    template: require('./zemCampaignLauncherGoal.component.html'),
    controller: function(
        $filter,
        zemConversionPixelsEndpoint,
        zemCampaignGoalsService
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
            return zemCampaignGoalsService.getAvailableGoals(
                [],
                campaignType,
                false
            );
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
