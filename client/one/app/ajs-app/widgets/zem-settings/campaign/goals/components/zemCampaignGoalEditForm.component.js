angular.module('one.widgets').component('zemCampaignGoalEditForm', {
    bindings: {
        campaignGoal: '=',
        availableGoals: '=',
        pixels: '=',
        newPixel: '=',
        errors: '=',
        isEdit: '=',
        onChange: '&?',
    },
    template: require('./zemCampaignGoalEditForm.component.html'),
    controller: function () {
        var $ctrl = this;

        $ctrl.updateTypeChange = updateTypeChange;
        $ctrl.propagateChange = propagateChange;
        $ctrl.clearErrors = clearErrors;
        $ctrl.prepareName = prepareName;
        $ctrl.isConversionGoalFormVisible = isConversionGoalFormVisible;
        $ctrl.isConversionPixelFormVisible = isConversionPixelFormVisible;
        $ctrl.isGAFormVisible = isGAFormVisible;
        $ctrl.isOmnitureFormVisible = isOmnitureFormVisible;
        $ctrl.setAvailableConversionWindowsForPixel = setAvailableConversionWindowsForPixel;

        $ctrl.$onInit = function () {
            $ctrl.campaignGoal = $ctrl.campaignGoal || {};
            $ctrl.goalUnit = getGoalUnit($ctrl.campaignGoal);
            $ctrl.conversionGoalTypes = options.conversionGoalTypes;
            $ctrl.conversionWindows = options.conversionWindows;
        };

        function updateTypeChange (goalUnit) {
            if ($ctrl.campaignGoal.type === constants.campaignGoalKPI.CPA) {
                $ctrl.campaignGoal.conversionGoal = $ctrl.campaignGoal.conversionGoal || {};
                delete $ctrl.campaignGoal.conversionGoal.goalId;
                delete $ctrl.campaignGoal.conversionGoal.conversionWindow;
            } else {
                delete $ctrl.campaignGoal.conversionGoal;
            }

            $ctrl.clearErrors('type');
            $ctrl.clearErrors('conversionGoal');

            if (goalUnit !== undefined || $ctrl.campaignGoal.type === constants.campaignGoalKPI.PAGES_PER_SESSION) {
                setDefaultValue();
            }
            $ctrl.goalUnit = goalUnit || '';
        }

        function propagateChange () {
            if ($ctrl.onChange) {
                var goal = null;
                if (!areRequiredFieldsEmpty()) {
                    goal = $ctrl.campaignGoal;
                }
                $ctrl.onChange({goal: goal});
            }
        }

        function clearErrors (name) {
            if (!$ctrl.errors) return;
            delete $ctrl.errors[name];
        }

        function prepareName (option) {
            if (!$ctrl.isEdit) return option && option.name || null;

            if ($ctrl.campaignGoal.type !== constants.campaignGoalKPI.CPA || !$ctrl.campaignGoal.conversionGoal.name) {
                return option.name;
            }
            return 'CPA - ' + $ctrl.campaignGoal.conversionGoal.name;
        }

        function isConversionGoalFormVisible () {
            return $ctrl.campaignGoal.type === constants.campaignGoalKPI.CPA;
        }

        function isConversionPixelFormVisible () {
            return $ctrl.campaignGoal.conversionGoal &&
                $ctrl.campaignGoal.conversionGoal.type === constants.conversionGoalType.PIXEL;
        }

        function isGAFormVisible () {
            return $ctrl.campaignGoal.conversionGoal &&
                $ctrl.campaignGoal.conversionGoal.type === constants.conversionGoalType.GA;
        }

        function isOmnitureFormVisible () {
            return $ctrl.campaignGoal.conversionGoal &&
                $ctrl.campaignGoal.conversionGoal.type === constants.conversionGoalType.OMNITURE;
        }

        function setAvailableConversionWindowsForPixel (pixel) {
            $ctrl.conversionWindows = pixel.conversionWindows;
        }

        function getGoalUnit (goal) {
            for (var i = 0; i < options.campaignGoalKPIs.length; i++) {
                var kpiDefault = options.campaignGoalKPIs[i];
                if (kpiDefault.value === goal.type) {
                    return kpiDefault.unit;
                }
            }
            return '';
        }

        function setDefaultValue () {
            if ($ctrl.isEdit) return;

            $ctrl.campaignGoal.value = null;
            defaults.campaignGoalKPI.forEach(function (kpiDefault) {
                if (kpiDefault.id === $ctrl.campaignGoal.type) {
                    $ctrl.campaignGoal.value = kpiDefault.value;
                }
            });
        }

        function areRequiredFieldsEmpty () {
            if (!$ctrl.campaignGoal.value || !$ctrl.campaignGoal.type) {
                return true;
            }

            return areRequiredConversionGoalFieldsEmpty();
        }

        function areRequiredConversionGoalFieldsEmpty () {
            if (!isConversionGoalFormVisible()) {
                return false;
            }

            if (!$ctrl.campaignGoal.conversionGoal.type || !$ctrl.campaignGoal.conversionGoal.goalId) {
                return true;
            }

            if (isConversionPixelFormVisible() && !$ctrl.campaignGoal.conversionGoal.conversionWindow) {
                return true;
            }

            return false;
        }
    },
});
