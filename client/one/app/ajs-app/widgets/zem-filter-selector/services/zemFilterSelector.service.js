angular
    .module('one.widgets')
    .service('zemFilterSelectorService', function(
        $rootScope,
        $state,
        $filter,
        zemPermissions,
        zemDataFilterService,
        zemFilterSelectorSharedService,
        zemMediaSourcesService,
        zemAgenciesService,
        zemPubSubService
    ) {
        // eslint-disable-line max-len
        this.init = init;
        this.getVisibleSections = getVisibleSections;
        this.getAppliedConditions = getAppliedConditions;
        this.applyFilter = applyFilter;
        this.removeAppliedCondition = removeAppliedCondition;
        this.toggleSelectAll = toggleSelectAll;

        this.onSectionsUpdate = onSectionsUpdate;

        // Section properties based on condition type:
        // - type: list (checkboxes)
        //     - options: array of objects with properties:
        //         - text: text displayed as checkbox input label,
        //         - value: checkbox value,
        //         - enabled: boolean defining if checkbox is checked,
        //         - [appliedConditionText]: text displayed in applied conditions when option is enabled
        // - type: value (radio buttons)
        //     - options: array of objects with properties:
        //         - text: text displayed as radio input label,
        //         - value: radio input value,
        //         - [appliedConditionText]: text displayed in applied conditions when option is enabled
        //     - value: radio input group model, value set to the value of enabled option from options array
        var FILTER_SECTIONS = [
            {
                condition: zemDataFilterService.CONDITIONS.sources,
                title: 'Filter by Media source',
                appliedConditionName: 'Media source',
                permissions: ['zemauth.can_filter_by_media_source'],
                cssClass: 'sources',
                getOptions: getSourcesOptions,
                isVisible: function() {
                    return $state.includes('v2.analytics');
                },
            },
            {
                condition: zemDataFilterService.CONDITIONS.agencies,
                title: 'Filter by Agency',
                appliedConditionName: 'Agency',
                cssClass: 'agencies',
                getOptions: getAgenciesOptions,
                permissions: ['zemauth.can_filter_by_agency'],
                isVisible: function() {
                    return (
                        $state.params.level ===
                        constants.levelStateParam.ACCOUNTS
                    );
                },
            },
            {
                condition: zemDataFilterService.CONDITIONS.accountTypes,
                title: 'Filter by Account type',
                appliedConditionName: 'Account type',
                cssClass: 'account-types',
                getOptions: getAccountTypesOptions,
                permissions: ['zemauth.can_filter_by_account_type'],
                isVisible: function() {
                    return (
                        $state.params.level ===
                        constants.levelStateParam.ACCOUNTS
                    );
                },
            },
            {
                condition: zemDataFilterService.CONDITIONS.businesses,
                title: 'Filter by Business',
                appliedConditionName: 'Business',
                cssClass: 'businesses',
                getOptions: getBusinessesOptions,
                permissions: ['zemauth.can_filter_by_business'],
                isVisible: function() {
                    return (
                        $state.params.level ===
                        constants.levelStateParam.ACCOUNTS
                    );
                },
            },
            {
                condition: zemDataFilterService.CONDITIONS.statuses,
                title: 'Filter by Status',
                appliedConditionName: 'Status',
                cssClass: 'statuses',
                getOptions: getStatusesOptions,
            },
            {
                condition: zemDataFilterService.CONDITIONS.publisherStatus,
                title: 'Filter by Publisher status',
                appliedConditionName: 'Publisher status',
                cssClass: 'publisher-statuses',
                getOptions: getPublisherStatusOptions,
                permissions: ['zemauth.can_see_publisher_blacklist_status'],
                isVisible: function() {
                    return (
                        $state.params.breakdown ===
                        constants.breakdownStateParam.PUBLISHERS
                    );
                },
            },
        ];

        var STATUSES_OPTIONS = [
            {
                value: zemDataFilterService.STATUSES_CONDITION_VALUES.archived,
                text: 'Show archived items',
                appliedConditionText: 'Show archived',
            },
        ];

        var PUBLISHER_STATUS_OPTIONS = [
            {
                value:
                    zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES.all,
                text: 'Show all publishers',
            },
            {
                value:
                    zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES
                        .active,
                text: 'Show active publishers only',
                appliedConditionText: 'Active',
            },
            {
                value:
                    zemDataFilterService.PUBLISHER_STATUS_CONDITION_VALUES
                        .blacklisted,
                text: 'Show blacklisted publishers only',
                appliedConditionText: 'Blacklisted',
            },
        ];

        var pubSub = zemPubSubService.createInstance();
        var EVENTS = {
            ON_SECTIONS_UPDATE:
                'zem-filter-selector-service-on-sections-update',
        };

        var availableSources;
        var availableAgencies;

        //
        // Public methods
        //
        function init() {
            zemMediaSourcesService.onSourcesUpdate(refreshAvailableSources);
            zemAgenciesService.onAgenciesUpdate(refreshAvailableAgencies);

            // Collapse filter selector when user navigates to different view and update visible categories and options
            $rootScope.$on('$zemStateChangeSuccess', function() {
                zemFilterSelectorSharedService.setSelectorExpanded(false);
                pubSub.notify(EVENTS.ON_SECTIONS_UPDATE, getVisibleSections());
            });
        }

        function getVisibleSections() {
            var visibleSections = [];
            FILTER_SECTIONS.forEach(function(section) {
                if (
                    section.permissions &&
                    !zemPermissions.hasPermission(section.permissions)
                )
                    return;
                if (section.isVisible && !section.isVisible()) return;

                section = angular.copy(section);
                section.options = section.getOptions();

                if (
                    section.condition.type ===
                    zemDataFilterService.CONDITION_TYPES.list
                ) {
                    section.allOptionsSelected = areAllSectionOptionsEnabled(
                        section.options
                    );
                }

                if (
                    section.condition.type ===
                    zemDataFilterService.CONDITION_TYPES.value
                ) {
                    // Add value property to section to be used as radio input group model
                    section.value = zemDataFilterService.getAppliedCondition(
                        section.condition
                    );
                }

                visibleSections.push(section);
            });
            return visibleSections;
        }

        function getAppliedConditions() {
            var appliedConditions = [];
            angular.forEach(
                zemDataFilterService.getAppliedConditions(true),
                function(conditionValue, conditionName) {
                    var section = findConditionSection(conditionName);
                    if (!section) return;

                    var sectionOptions = section.getOptions();
                    if (!sectionOptions || sectionOptions.length === 0) return;

                    switch (section.condition.type) {
                        case zemDataFilterService.CONDITION_TYPES.value:
                            appliedConditions.push({
                                name: section.appliedConditionName,
                                text: getOptionTextForValue(
                                    sectionOptions,
                                    conditionValue
                                ),
                                condition: section.condition,
                            });
                            break;
                        case zemDataFilterService.CONDITION_TYPES.list:
                            var enabledOptions = [];
                            conditionValue.forEach(function(option) {
                                enabledOptions.push({
                                    name: section.appliedConditionName,
                                    text: getOptionTextForValue(
                                        sectionOptions,
                                        option
                                    ),
                                    value: option,
                                    condition: section.condition,
                                });
                            });
                            appliedConditions = appliedConditions.concat(
                                enabledOptions
                            );
                            break;
                    }
                }
            );
            return appliedConditions;
        }

        function applyFilter(visibleSections) {
            var conditions = [];
            angular.forEach(visibleSections, function(section) {
                var value;
                switch (section.condition.type) {
                    case zemDataFilterService.CONDITION_TYPES.value:
                        value = section.value || null;
                        break;
                    case zemDataFilterService.CONDITION_TYPES.list:
                        value = null;
                        if (section.options) {
                            value = [];
                            section.options.forEach(function(option) {
                                if (option.enabled) {
                                    value.push(option.value);
                                }
                            });
                        }
                        break;
                }

                if (value) {
                    conditions.push({
                        condition: section.condition,
                        value: value,
                    });
                }
            });

            zemDataFilterService.applyConditions(conditions);
        }

        function removeAppliedCondition(condition, value) {
            if (value) {
                zemDataFilterService.removeValueFromConditionList(
                    condition,
                    value
                );
            } else {
                zemDataFilterService.resetCondition(condition);
            }
        }

        function toggleSelectAll(section) {
            section.allOptionsSelected = !section.allOptionsSelected;
            section.options.map(function(option) {
                option.enabled = section.allOptionsSelected;
            });
        }

        //
        // Events
        //
        function onSectionsUpdate(callback) {
            return pubSub.register(EVENTS.ON_SECTIONS_UPDATE, callback);
        }

        //
        // Private methods
        //
        function findConditionSection(conditionName) {
            var visibleSections = getVisibleSections();
            for (var i = 0; i < visibleSections.length; i++) {
                if (visibleSections[i].condition.name === conditionName) {
                    return visibleSections[i];
                }
            }
        }

        function getOptionTextForValue(options, value) {
            if (!options) return;
            for (var i = 0; i < options.length; i++) {
                if (options[i].value === value) {
                    return (
                        options[i].appliedConditionText || options[i].text || ''
                    );
                }
            }
        }

        function areAllSectionOptionsEnabled(options) {
            if (!options) return;

            for (var i = 0; i < options.length; i++) {
                if (!options[i].enabled) return false;
            }
            return true;
        }

        function getSourcesOptions() {
            if (!availableSources) {
                refreshAvailableSources();
                return;
            }

            var sourcesOptions = availableSources.map(function(source) {
                source.enabled =
                    zemDataFilterService
                        .getFilteredSources()
                        .indexOf(source.value) !== -1;
                return source;
            });
            sourcesOptions = $filter('orderBy')(sourcesOptions, 'text');

            return sourcesOptions;
        }

        function getAgenciesOptions() {
            if (!availableAgencies) {
                refreshAvailableAgencies();
                return;
            }

            var agenciesOptions = availableAgencies.map(function(agency) {
                agency.enabled =
                    zemDataFilterService
                        .getFilteredAgencies()
                        .indexOf(agency.value) !== -1;
                return agency;
            });

            agenciesOptions = $filter('orderBy')(agenciesOptions, 'text');
            return agenciesOptions;
        }

        function getAccountTypesOptions() {
            var availableAccountTypes = [];
            options.accountTypes.forEach(function(accountType) {
                var accountTypeId = String(accountType.value);
                availableAccountTypes.push({
                    value: accountTypeId,
                    text: accountType.name,
                    enabled:
                        zemDataFilterService
                            .getFilteredAccountTypes()
                            .indexOf(accountTypeId) !== -1,
                });
            });
            return availableAccountTypes;
        }

        function getBusinessesOptions() {
            var availableBusinesses = [];
            options.businesses.forEach(function(business) {
                var businessId = String(business.value);
                availableBusinesses.push({
                    value: businessId,
                    text: business.name,
                    enabled:
                        zemDataFilterService
                            .getFilteredBusinesses()
                            .indexOf(businessId) !== -1,
                });
            });
            return availableBusinesses;
        }

        function getStatusesOptions() {
            return STATUSES_OPTIONS.map(function(status) {
                status.enabled =
                    zemDataFilterService
                        .getFilteredStatuses()
                        .indexOf(status.value) !== -1;
                return status;
            });
        }

        function getPublisherStatusOptions() {
            return PUBLISHER_STATUS_OPTIONS;
        }

        function refreshAvailableSources() {
            zemMediaSourcesService
                .getAvailableSources()
                .then(function(sources) {
                    availableSources = sources.map(function(source) {
                        return {value: source.id, text: source.name};
                    });
                    pubSub.notify(
                        EVENTS.ON_SECTIONS_UPDATE,
                        getVisibleSections()
                    );
                });
        }

        function refreshAvailableAgencies() {
            zemAgenciesService.getAgencies().then(function(agencies) {
                availableAgencies = agencies.map(function(agency) {
                    return {value: agency.id, text: agency.name};
                });
                pubSub.notify(EVENTS.ON_SECTIONS_UPDATE, getVisibleSections());
            });
        }
    });
