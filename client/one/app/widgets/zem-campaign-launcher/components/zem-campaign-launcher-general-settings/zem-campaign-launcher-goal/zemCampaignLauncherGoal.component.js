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
        $ctrl.formatGoalValue = formatGoalValue;

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

        function formatGoalValue (goal) {
            var value = $filter('number')(goal.value, 2);
            if (goal.type === constants.campaignGoalKPI.CPC) {
                value = $filter('number')(goal.value, 3);
            }

            if ([
                constants.campaignGoalKPI.CPA,
                constants.campaignGoalKPI.CPC,
                constants.campaignGoalKPI.CPM,
                constants.campaignGoalKPI.CPV,
                constants.campaignGoalKPI.CP_NON_BOUNCED_VISIT
            ].indexOf(goal.type) > -1) {
                return '$' + value + ' ' + constants.campaignGoalValueText[goal.type];
            } else if ([
                constants.campaignGoalKPI.TIME_ON_SITE,
                constants.campaignGoalKPI.MAX_BOUNCE_RATE,
                constants.campaignGoalKPI.PAGES_PER_SESSION,
                constants.campaignGoalKPI.NEW_UNIQUE_VISITORS
            ].indexOf(goal.type) > -1) {
                return value + ' ' + constants.campaignGoalValueText[goal.type];
            }
        }

        function getPixelsWithConversionWindows (pixels) {
            pixels.forEach(function (pixel) {
                pixel.conversionWindows = options.conversionWindows;
            });
            return pixels;
        }
    },
});
