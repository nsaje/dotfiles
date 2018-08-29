var constantsHelpers = require('../../../../../../shared/helpers/constants.helpers');

angular.module('one.widgets').component('zemCampaignGoalEditForm', {
    bindings: {
        campaignGoal: '=',
        availableGoals: '=',
        goalsDefaults: '<',
        pixels: '=',
        newPixel: '=',
        errors: '=',
        isEdit: '=',
        onChange: '&?',
    },
    template: require('./zemCampaignGoalEditForm.component.html'),
    controller: function(zemNavigationNewService, zemMulticurrencyService) {
        var $ctrl = this;
        var activeAccount;

        $ctrl.updateTypeChange = updateTypeChange;
        $ctrl.propagateChange = propagateChange;
        $ctrl.clearErrors = clearErrors;
        $ctrl.prepareName = prepareName;
        $ctrl.isConversionGoalFormVisible = isConversionGoalFormVisible;
        $ctrl.isConversionPixelFormVisible = isConversionPixelFormVisible;
        $ctrl.isGAFormVisible = isGAFormVisible;
        $ctrl.isOmnitureFormVisible = isOmnitureFormVisible;
        $ctrl.setAvailableConversionWindowsForPixel = setAvailableConversionWindowsForPixel;

        $ctrl.$onInit = function() {
            activeAccount = zemNavigationNewService.getActiveAccount();
            $ctrl.campaignGoal = $ctrl.campaignGoal || {};
            $ctrl.goalUnit = getGoalUnit($ctrl.campaignGoal);
            $ctrl.conversionGoalTypes = options.conversionGoalTypes;
            $ctrl.conversionWindows = options.conversionWindows;
        };

        function updateTypeChange(goalUnit) {
            if ($ctrl.campaignGoal.type === constants.campaignGoalKPI.CPA) {
                $ctrl.campaignGoal.conversionGoal =
                    $ctrl.campaignGoal.conversionGoal || {};
                delete $ctrl.campaignGoal.conversionGoal.goalId;
                delete $ctrl.campaignGoal.conversionGoal.conversionWindow;
            } else {
                delete $ctrl.campaignGoal.conversionGoal;
            }

            $ctrl.clearErrors('type');
            $ctrl.clearErrors('conversionGoal');

            if (
                goalUnit !== undefined ||
                $ctrl.campaignGoal.type ===
                    constants.campaignGoalKPI.PAGES_PER_SESSION
            ) {
                setDefaultValue();
            }
            $ctrl.goalUnit = goalUnit || '';
        }

        function propagateChange() {
            if ($ctrl.onChange) {
                var goal = null;
                if (!areRequiredFieldsEmpty()) {
                    goal = $ctrl.campaignGoal;
                }
                $ctrl.onChange({goal: goal});
            }
        }

        function clearErrors(name) {
            if (!$ctrl.errors) return;
            delete $ctrl.errors[name];
        }

        function prepareName(option) {
            if (!$ctrl.isEdit) return (option && option.name) || null;

            if (
                $ctrl.campaignGoal.type !== constants.campaignGoalKPI.CPA ||
                !$ctrl.campaignGoal.conversionGoal.name
            ) {
                return option.name;
            }
            return 'CPA - ' + $ctrl.campaignGoal.conversionGoal.name;
        }

        function isConversionGoalFormVisible() {
            return $ctrl.campaignGoal.type === constants.campaignGoalKPI.CPA;
        }

        function isConversionPixelFormVisible() {
            return (
                $ctrl.campaignGoal.conversionGoal &&
                $ctrl.campaignGoal.conversionGoal.type ===
                    constants.conversionGoalType.PIXEL
            );
        }

        function isGAFormVisible() {
            return (
                $ctrl.campaignGoal.conversionGoal &&
                $ctrl.campaignGoal.conversionGoal.type ===
                    constants.conversionGoalType.GA
            );
        }

        function isOmnitureFormVisible() {
            return (
                $ctrl.campaignGoal.conversionGoal &&
                $ctrl.campaignGoal.conversionGoal.type ===
                    constants.conversionGoalType.OMNITURE
            );
        }

        function setAvailableConversionWindowsForPixel(pixel) {
            $ctrl.conversionWindows = pixel.conversionWindows;
        }

        function getGoalUnit(goal) {
            for (var i = 0; i < options.campaignGoalKPIs.length; i++) {
                var kpiDefault = options.campaignGoalKPIs[i];
                if (kpiDefault.value === goal.type) {
                    if (kpiDefault.unit !== '__CURRENCY__') {
                        return kpiDefault.unit;
                    }

                    return zemMulticurrencyService.getAppropriateCurrencySymbol(
                        activeAccount
                    );
                }
            }
            return '';
        }

        function setDefaultValue() {
            if ($ctrl.isEdit || !$ctrl.goalsDefaults) return;

            var kpiName = constantsHelpers.convertToName(
                $ctrl.campaignGoal.type,
                constants.campaignGoalKPI
            );
            $ctrl.campaignGoal.value = $ctrl.goalsDefaults[kpiName] || null;
        }

        function areRequiredFieldsEmpty() {
            if (!$ctrl.campaignGoal.value || !$ctrl.campaignGoal.type) {
                return true;
            }

            return areRequiredConversionGoalFieldsEmpty();
        }

        function areRequiredConversionGoalFieldsEmpty() {
            if (!isConversionGoalFormVisible()) {
                return false;
            }

            if (
                !$ctrl.campaignGoal.conversionGoal.type ||
                !$ctrl.campaignGoal.conversionGoal.goalId
            ) {
                return true;
            }

            if (
                isConversionPixelFormVisible() &&
                !$ctrl.campaignGoal.conversionGoal.conversionWindow
            ) {
                return true;
            }

            return false;
        }
    },
});
