require('./zemCampaignLauncherGoal.component.less');

angular.module('one.widgets').component('zemCampaignLauncherGoal', {
    bindings: {
        stateService: '<',
        account: '<',
    },
    template: require('./zemCampaignLauncherGoal.component.html'),
    controller: function ($filter, zemConversionPixelsEndpoint, zemMulticurrencyService) {
        var $ctrl = this;

        $ctrl.updateCampaignGoal = updateCampaignGoal;

        $ctrl.$onInit = function () {
            $ctrl.state = $ctrl.stateService.getState();
            $ctrl.availableGoals = angular.copy(options.campaignGoalKPIs).map(function (goalKPI) {
                if (goalKPI.unit === '__CURRENCY__') {
                    goalKPI.unit = zemMulticurrencyService.getAppropriateCurrencySymbol($ctrl.account);
                }
                return goalKPI;
            });
            $ctrl.goalsDefaults = $ctrl.stateService.getCampaignGoalsDefaults();

            $ctrl.pixels = {};

            if ($ctrl.state.fields.campaignGoal) {
                $ctrl.newCampaignGoal = angular.copy($ctrl.state.fields.campaignGoal);
            } else {
                $ctrl.newCampaignGoal = {primary: true};
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

        function updateCampaignGoal (goal) {
            $ctrl.state.fields.campaignGoal = goal;
            $ctrl.stateService.validateFields();
        }

        function getPixelsWithConversionWindows (pixels) {
            pixels.forEach(function (pixel) {
                pixel.conversionWindows = options.conversionWindows;
            });
            return pixels;
        }
    },
});
