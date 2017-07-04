angular.module('one.widgets').service('zemCampaignLauncherStateService', function ($timeout, zemCampaignLauncherEndpoint, zemNavigationNewService) { // eslint-disable-line max-len
    var LAUNCHER_STEPS = {
        objectives: {
            title: 'What is your objective?',
            stepIndicatorTitle: 'Objective',
            description: 'Select your campaign\'s objective.',
        },
        generalSettings: {
            title: 'Campaign settings',
            stepIndicatorTitle: 'Settings',
            description: 'Enter your campaign\'s general settings.',
            fields: [
                {name: 'campaignName', required: true},
                {name: 'iabCategory', required: true},
                {name: 'startDate', required: true},
                {name: 'endDate', required: true},
                {name: 'budgetAmount', required: true},
                {name: 'maxCpc', required: false},
                {name: 'dailyBudget', required: true},
                {name: 'campaignGoal', required: true},
            ],
            controls: {
                previous: true,
                next: true,
                review: true,
            }
        },
        review: {
            title: 'Review & Launch',
            stepIndicatorTitle: 'Review & Launch',
            description: 'Review and launch campaign.',
            controls: {
                previous: true,
                launch: true,
            }
        },
    };

    function zemCampaignLauncherStateService (account) {
        var state = {
            steps: {},
            orderedSteps: [],
            currentStep: null,
            campaignObjective: null,
            fields: {},
            fieldsErrors: {},
            requests: {
                validate: {},
                launchCampaign: {},
            },
        };

        this.getState = getState;
        this.initialize = initialize;
        this.goToStep = goToStep;
        this.goToStepWithIndex = goToStepWithIndex;
        this.initLauncherWithObjective = initLauncherWithObjective;
        this.validateFields = validateFields;
        this.areStepFieldsValid = areStepFieldsValid;
        this.areAllStepsValid = areAllStepsValid;
        this.launchCampaign = launchCampaign;

        function initialize () {
            initLauncherWithObjective();
            state.currentStep = state.orderedSteps[0];
        }

        function getState () {
            return state;
        }

        function goToStep (step) {
            goToStepWithIndex(state.orderedSteps.indexOf(step));
        }

        function goToStepWithIndex (index) {
            if (state.orderedSteps[index]) {
                state.currentStep = state.orderedSteps[index];
            }
        }

        function initLauncherWithObjective (objective) {
            if (state.campaignObjective !== objective) {
                state.campaignObjective = objective || null;
                state.steps = angular.copy(LAUNCHER_STEPS),
                state.orderedSteps = getOrderedSteps(state.steps, objective);
                state.fields = getEmptyFields(state.orderedSteps);
                state.fieldsErrors = angular.copy(state.fields);
            }

            if (state.campaignObjective && state.orderedSteps.length > 1) {
                state.currentStep = state.orderedSteps[1];
            }
        }

        function validateFields () {
            var fields = {};
            angular.forEach(state.fields, function (value, name) {
                if (value !== null) {
                    fields[name] = value;
                }
            });
            state.requests.validate.inProgress = true;
            var validationPromise = state.requests.validate.promise =
                zemCampaignLauncherEndpoint.validate(account, fields)
                .then(function () {
                    if (validationPromise !== state.requests.validate.promise) return; // There's a more recent request
                    angular.forEach(fields, function (value, name) {
                        state.fieldsErrors[name] = null;
                    });
                })
                .catch(function (errors) {
                    if (validationPromise !== state.requests.validate.promise) return; // There's a more recent request
                    state.fieldsErrors = errors;
                })
                .finally(function () {
                    state.requests.validate.inProgress = false;
                });

            return validationPromise;
        }

        function areStepFieldsValid (step) {
            if (!step.fields) return true;

            for (var i = 0; i < step.fields.length; i++) {
                var field = step.fields[i];
                if (state.fieldsErrors[field.name] && state.fieldsErrors[field.name].length !== 0) {
                    return false;
                }
                if (field.required && !state.fields[field.name]) {
                    return false;
                }
            }
            return true;
        }

        function areAllStepsValid () {
            for (var i = 0; i < state.orderedSteps.length; i++) {
                if (!areStepFieldsValid(state.orderedSteps[i])) return false;
            }
            return true;
        }

        function launchCampaign () {
            if (state.requests.launchCampaign.inProgress) return;

            state.requests.launchCampaign.inProgress = true;
            zemCampaignLauncherEndpoint.launchCampaign(account, state.fields)
                .then(function (campaignId) {
                    state.requests.launchCampaign.success = true;
                    $timeout(function () {
                        // FIXME (jurebajt): New campaign isn't available in navigation hierarchy
                        var launchedCampaign = zemNavigationNewService.getEntityById(
                            constants.entityType.CAMPAIGN, campaignId
                        );
                        zemNavigationNewService.navigateTo(launchedCampaign);
                    }, 2000);
                })
                .catch(function (errors) {
                    state.requests.launchCampaign.error = true;
                    state.fieldsErrors = errors;
                    $timeout(function () {
                        state.requests.launchCampaign.error = false;
                    }, 5000);
                })
                .finally(function () {
                    state.requests.launchCampaign.inProgress = false;
                });
        }

        function getOrderedSteps (steps, objective) {
            var orderedSteps = [steps.objectives];

            if (objective) {
                orderedSteps = orderedSteps.concat(getDefaultOrderedSteps(steps));
            }

            return orderedSteps;
        }

        function getDefaultOrderedSteps (steps) {
            return [
                steps.generalSettings,
                steps.review,
            ];
        }

        function getEmptyFields (steps) {
            var fields = {};
            angular.forEach(steps, function (step) {
                if (!step.fields) return;

                step.fields.forEach(function (field) {
                    fields[field.name] = null;
                });
            });
            return fields;
        }
    }

    return {
        createInstance: function (account) {
            return new zemCampaignLauncherStateService(account);
        }
    };
});
