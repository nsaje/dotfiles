var constantsHelpers = require('../../../shared/helpers/constants.helpers');

angular
    .module('one.widgets')
    .service('zemCampaignLauncherStateService', function(
        $timeout,
        $state,
        $window,
        zemCampaignLauncherEndpoint
    ) {
        // eslint-disable-line max-len
        var LAUNCHER_STEPS = {
            objectives: {
                title: 'Campaign launcher',
                stepIndicatorTitle: 'Objective',
            },
            generalSettings: {
                title: 'Campaign settings',
                stepIndicatorTitle: 'Settings',
                fields: [
                    {name: 'campaignName', required: true},
                    {name: 'iabCategory', required: true},
                    {name: 'language', required: true},
                    {name: 'budgetAmount', required: true},
                    {name: 'maxCpc', required: false},
                    {name: 'dailyBudget', required: true},
                    {name: 'campaignGoal', required: true},
                    {name: 'type', required: true},
                ],
                controls: {
                    previous: true,
                    next: true,
                    review: true,
                },
            },
            creatives: {
                title: 'Campaign creatives',
                stepIndicatorTitle: 'Creatives',
                fields: [{name: 'uploadBatch', required: true}],
                controls: {
                    previous: true,
                    next: true,
                    review: true,
                },
            },
            targeting: {
                title: 'Campaign targeting',
                stepIndicatorTitle: 'Targeting',
                fields: [
                    {name: 'targetRegions', required: false},
                    {name: 'exclusionTargetRegions', required: false},
                    {name: 'targetDevices', required: false},
                    {name: 'targetOs', required: false},
                    {name: 'targetPlacements', required: false},
                ],
                controls: {
                    previous: true,
                    next: true,
                    review: true,
                },
            },
            review: {
                title: 'Congratulations, you are all set!',
                stepIndicatorTitle: 'Review & Launch',
                controls: {
                    previous: true,
                    launch: true,
                },
            },
        };

        function zemCampaignLauncherStateService(account) {
            var state = {
                steps: {},
                orderedSteps: [],
                currentStep: null,
                campaignObjective: null,
                creatives: {},
                fields: {},
                fieldsErrors: {},
                requests: {
                    getDefaults: {},
                    validate: {},
                    createCreativesBatch: {},
                    launchCampaign: {},
                },
            };
            var defaults = {};

            this.getState = getState;
            this.initialize = initialize;
            this.goToStep = goToStep;
            this.goToStepWithIndex = goToStepWithIndex;
            this.initLauncherWithObjective = initLauncherWithObjective;
            this.validateFields = validateFields;
            this.areStepFieldsValid = areStepFieldsValid;
            this.areAllStepsValid = areAllStepsValid;
            this.launchCampaign = launchCampaign;
            this.getCampaignGoalsDefaults = getCampaignGoalsDefaults;

            function initialize() {
                state.requests.getDefaults = {
                    inProgress: true,
                };
                zemCampaignLauncherEndpoint
                    .getDefaults(account)
                    .then(function(response) {
                        defaults = response;
                        initLauncherWithObjective();
                        state.requests.getDefaults.success = true;
                    })
                    .catch(function() {
                        state.requests.getDefaults.error = true;
                    })
                    .finally(function() {
                        state.requests.getDefaults.inProgress = false;
                    });
            }

            function getState() {
                return state;
            }

            function goToStep(step) {
                goToStepWithIndex(state.orderedSteps.indexOf(step));
            }

            function goToStepWithIndex(index) {
                if (state.orderedSteps[index]) {
                    state.currentStep = state.orderedSteps[index];
                }
            }

            function initLauncherWithObjective(objective) {
                if (
                    !state.campaignObjective ||
                    state.campaignObjective !== objective
                ) {
                    state.campaignObjective = objective || null;
                    state.steps = angular.copy(LAUNCHER_STEPS);
                    state.orderedSteps = getOrderedSteps(state.steps);
                    state.fields = getDefaultFields(state.orderedSteps);
                    state.fieldsErrors = angular.copy(state.fields);

                    state.fields.type = constantsHelpers.convertToName(
                        objective || constants.campaignTypes.CONTENT,
                        constants.campaignTypes
                    );
                }

                var stepIndex = 0;
                if (state.campaignObjective && state.orderedSteps.length > 1) {
                    stepIndex = 1;
                }
                goToStepWithIndex(stepIndex);
            }

            function validateFields() {
                var fields = {};
                angular.forEach(state.fields, function(value, name) {
                    if (value) {
                        fields[name] = value;
                    }
                });
                state.requests.validate.inProgress = true;
                var validationPromise = (state.requests.validate.promise = zemCampaignLauncherEndpoint
                    .validate(account, fields)
                    .then(function() {
                        if (
                            validationPromise !==
                            state.requests.validate.promise
                        ) {
                            return; // There's a more recent request
                        }
                        state.fieldsErrors = {};
                        angular.forEach(fields, function(value, name) {
                            state.fieldsErrors[name] = null;
                        });
                    })
                    .catch(function(errors) {
                        if (
                            validationPromise !==
                            state.requests.validate.promise
                        ) {
                            return; // There's a more recent request
                        }
                        state.fieldsErrors =
                            errors && errors.details ? errors.details : {};
                    })
                    .finally(function() {
                        state.requests.validate.inProgress = false;
                    }));

                return validationPromise;
            }

            function areStepFieldsValid(step) {
                if (!step || !step.fields) return true;

                for (var i = 0; i < step.fields.length; i++) {
                    var field = step.fields[i];
                    if (
                        state.fieldsErrors[field.name] &&
                        state.fieldsErrors[field.name].length !== 0
                    ) {
                        return false;
                    }
                    if (field.required && !state.fields[field.name]) {
                        return false;
                    }
                }
                return true;
            }

            function areAllStepsValid() {
                for (var i = 0; i < state.orderedSteps.length; i++) {
                    if (!areStepFieldsValid(state.orderedSteps[i]))
                        return false;
                }
                return true;
            }

            function launchCampaign() {
                if (state.requests.launchCampaign.inProgress) return;

                var fields = {};
                angular.forEach(state.fields, function(value, name) {
                    fields[name] = value || null;
                });

                state.requests.launchCampaign.inProgress = true;
                zemCampaignLauncherEndpoint
                    .launchCampaign(account, fields)
                    .then(function(campaignId) {
                        state.requests.launchCampaign.success = true;
                        $timeout(function() {
                            var params = {
                                level: constants.levelStateParam.CAMPAIGN,
                                id: campaignId,
                            };
                            var url = $state.href('v2.analytics', params);
                            $window.location.assign(url);
                        }, 2000);
                    })
                    .catch(function(errors) {
                        if (errors && errors.details) {
                            if (angular.isArray(errors.details)) {
                                state.requests.launchCampaign.errorMsgs =
                                    errors.details;
                                state.fieldsErrors = {};
                            } else {
                                state.requests.launchCampaign.errorMsgs = null;
                                state.fieldsErrors = errors.details;
                            }
                        }
                        state.requests.launchCampaign.error = true;
                        $timeout(function() {
                            state.requests.launchCampaign.error = false;
                        }, 5000);
                    })
                    .finally(function() {
                        state.requests.launchCampaign.inProgress = false;
                    });
            }

            function getCampaignGoalsDefaults() {
                return defaults.goalsDefaults;
            }

            function getOrderedSteps(steps) {
                return [
                    steps.objectives,
                    steps.generalSettings,
                    steps.creatives,
                    steps.targeting,
                    steps.review,
                ];
            }

            function getDefaultFields(steps) {
                var fields = {};
                angular.forEach(steps, function(step) {
                    if (!step.fields) return;

                    step.fields.forEach(function(field) {
                        fields[field.name] = defaults[field.name] || null;
                    });
                });
                return fields;
            }
        }

        return {
            createInstance: function(account) {
                return new zemCampaignLauncherStateService(account);
            },
        };
    });
