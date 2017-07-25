angular.module('one.widgets').component('zemCampaignLauncherGoal', {
    bindings: {
        stateService: '<',
        account: '<',
    },
    template: require('./zemCampaignLauncherGoal.component.html'),
    controller: function ($filter, zemConversionPixelsEndpoint) {
        var $ctrl = this;
        var campaignEditFormVisible = true;

        $ctrl.isCampaignGoalEditFormVisible = isCampaignGoalEditFormVisible;
        $ctrl.showCampaignGoalEditForm = showCampaignGoalEditForm;
        $ctrl.submitCampaignGoal = submitCampaignGoal;

        $ctrl.$onInit = function () {
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.availableGoals = angular.copy(options.campaignGoalKPIs);
            $ctrl.pixels = {};

            if ($ctrl.state.fields.campaignGoal) {
                $ctrl.newCampaignGoal = angular.copy($ctrl.state.fields.campaignGoal);
                campaignEditFormVisible = false;
            } else {
                $ctrl.newCampaignGoal = {primary: true, conversionGoal: {}};
            }

            $ctrl.pixels.loading = true;
            zemConversionPixelsEndpoint.list($ctrl.account.id)
                .then(function (data) {
                    var availablePixels = data.rows.filter(function (pixel) {
                        return !pixel.archived;
                    });
                    $ctrl.pixels.list = getPixelsWithConversionWindows(availablePixels);
                    $ctrl.pixels.loading = false;
                });
        };

        function isCampaignGoalEditFormVisible () {
            return campaignEditFormVisible || $ctrl.state.fieldsErrors.campaignGoal;
        }

        function showCampaignGoalEditForm () {
            $ctrl.newCampaignGoal = $ctrl.state.fields.campaignGoal;
            campaignEditFormVisible = true;
        }

        function submitCampaignGoal () {
            $ctrl.state.fields.campaignGoal = $ctrl.newCampaignGoal;
            $ctrl.stateService.validateFields().finally(function () {
                campaignEditFormVisible = false;
            });
        }

        function getPixelsWithConversionWindows (pixels) {
            pixels.forEach(function (pixel) {
                pixel.conversionWindows = options.conversionWindows;
            });
            return pixels;
        }
    },
});
