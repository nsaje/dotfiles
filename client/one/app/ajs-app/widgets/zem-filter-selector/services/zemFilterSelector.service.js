var RoutePathName = require('../../../../app.constants').RoutePathName;
var routerHelpers = require('../../../../shared/helpers/router.helpers');

angular
    .module('one.widgets')
    .service('zemFilterSelectorService', function(
        $rootScope,
        NgRouter,
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
        this.destroy = destroy;
        this.getVisibleSections = getVisibleSections;
        this.getAppliedConditions = getAppliedConditions;
        this.applyFilter = applyFilter;
        this.removeAppliedCondition = removeAppliedCondition;
        this.toggleSelectAll = toggleSelectAll;
        this.resetAllConditions = resetAllConditions;

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
                    return NgRouter.url.includes(
                        RoutePathName.APP_BASE + '/' + RoutePathName.ANALYTICS
                    );
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
                    var activatedRoute = routerHelpers.getActivatedRoute(
                        NgRouter
                    );
                    return (
                        NgRouter.url.includes(
                            RoutePathName.APP_BASE +
                                '/' +
                                RoutePathName.ANALYTICS
                        ) &&
                        activatedRoute.snapshot.data.level ===
                            constants.levelParam.ACCOUNTS
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
                    var activatedRoute = routerHelpers.getActivatedRoute(
                        NgRouter
                    );
                    return (
                        NgRouter.url.includes(
                            RoutePathName.APP_BASE +
                                '/' +
                                RoutePathName.ANALYTICS
                        ) &&
                        activatedRoute.snapshot.data.level ===
                            constants.levelParam.ACCOUNTS
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
                    var activatedRoute = routerHelpers.getActivatedRoute(
                        NgRouter
                    );
                    return (
                        NgRouter.url.includes(
                            RoutePathName.APP_BASE +
                                '/' +
                                RoutePathName.ANALYTICS
                        ) &&
                        activatedRoute.snapshot.data.level ===
                            constants.levelParam.ACCOUNTS
                    );
                },
            },
            {
                condition: zemDataFilterService.CONDITIONS.statuses,
                title: 'Filter by Status',
                appliedConditionName: 'Status',
                cssClass: 'statuses',
                getOptions: getStatusesOptions,
                isVisible: function() {
                    return (
                        NgRouter.url.includes(
                            RoutePathName.APP_BASE +
                                '/' +
                                RoutePathName.ANALYTICS
                        ) ||
                        NgRouter.url.includes(
                            RoutePathName.APP_BASE +
                                '/' +
                                RoutePathName.PIXELS_LIBRARY
                        )
                    );
                },
            },
            {
                condition: zemDataFilterService.CONDITIONS.publisherStatus,
                title: 'Filter by Publisher status',
                appliedConditionName: 'Publisher status',
                cssClass: 'publisher-statuses',
                getOptions: getPublisherStatusOptions,
                permissions: ['zemauth.can_see_publisher_blacklist_status'],
                isVisible: function() {
                    var activatedRoute = routerHelpers.getActivatedRoute(
                        NgRouter
                    );
                    return (
                        NgRouter.url.includes(
                            RoutePathName.APP_BASE +
                                '/' +
                                RoutePathName.ANALYTICS
                        ) &&
                        (activatedRoute.snapshot.params.breakdown ===
                            constants.breakdownParam.PUBLISHERS ||
                            activatedRoute.snapshot.params.breakdown ===
                                constants.breakdownParam.PLACEMENTS)
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

        var mediaSourcesUpdateHandler,
            agenciesUpdateHandler,
            dataFilterUpdateHandler;

        //
        // Public methods
        //
        function init() {
            mediaSourcesUpdateHandler = zemMediaSourcesService.onSourcesUpdate(
                refreshAvailableSources
            );
            agenciesUpdateHandler = zemAgenciesService.onAgenciesUpdate(
                refreshAvailableAgencies
            );
            dataFilterUpdateHandler = zemDataFilterService.onDataFilterUpdate(
                function() {
                    pubSub.notify(EVENTS.ON_SECTIONS_UPDATE);
                }
            );

            $rootScope.$on('$zemNavigationEnd', function() {
                initFromUrlParams();
                zemFilterSelectorSharedService.setSelectorExpanded(false);
                pubSub.notify(EVENTS.ON_SECTIONS_UPDATE);
            });

            initFromUrlParams();
            zemFilterSelectorSharedService.setSelectorExpanded(false);
            pubSub.notify(EVENTS.ON_SECTIONS_UPDATE);
        }

        function destroy() {
            if (mediaSourcesUpdateHandler) mediaSourcesUpdateHandler();
            if (agenciesUpdateHandler) agenciesUpdateHandler();
            if (dataFilterUpdateHandler) dataFilterUpdateHandler();
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

        function getAppliedConditions(visibleSections) {
            var appliedConditions = [];
            angular.forEach(
                zemDataFilterService.getAppliedConditions(),
                function(conditionValue, conditionName) {
                    var section = findConditionInVisibleSections(
                        conditionName,
                        visibleSections
                    );
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
            var appliedConditions = [];
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
                    appliedConditions.push({
                        condition: section.condition,
                        value: value,
                    });
                }
            });
            zemDataFilterService.applyConditions(appliedConditions);
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

        function resetAllConditions() {
            zemDataFilterService.resetAllConditions();
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

        function initFromUrlParams() {
            var activatedRoute = routerHelpers.getActivatedRoute(NgRouter);
            var queryParams = activatedRoute.snapshot.queryParams;

            var appliedConditions = [];
            angular.forEach(zemDataFilterService.CONDITIONS, function(
                condition
            ) {
                var param = queryParams[condition.urlParam];
                if (param) {
                    appliedConditions.push({
                        condition: condition,
                        value: param,
                    });
                }
            });

            if (appliedConditions.length > 0) {
                zemDataFilterService.applyConditions(appliedConditions);
            } else {
                zemDataFilterService.resetAllConditions();
            }
        }

        function findConditionInVisibleSections(
            conditionName,
            visibleSections
        ) {
            for (var i = 0; i < (visibleSections || []).length; i++) {
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

        var refreshAvailableSourcesFired = false;
        function getSourcesOptions() {
            if (!availableSources && !refreshAvailableSourcesFired) {
                refreshAvailableSources();
                refreshAvailableSourcesFired = true;
                return;
            }

            var sourcesOptions = (availableSources || []).map(function(source) {
                source.enabled =
                    zemDataFilterService
                        .getFilteredSources()
                        .indexOf(source.value) !== -1;
                return source;
            });
            sourcesOptions = $filter('orderBy')(sourcesOptions, 'text');

            return sourcesOptions;
        }

        var refreshAvailableAgenciesFired = false;
        function getAgenciesOptions() {
            if (!availableAgencies && !refreshAvailableAgenciesFired) {
                refreshAvailableAgencies();
                refreshAvailableAgenciesFired = true;
                return;
            }

            var agenciesOptions = (availableAgencies || []).map(function(
                agency
            ) {
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
                    pubSub.notify(EVENTS.ON_SECTIONS_UPDATE);
                });
        }

        function refreshAvailableAgencies() {
            zemAgenciesService.getAgencies().then(function(agencies) {
                availableAgencies = agencies.map(function(agency) {
                    return {value: agency.id, text: agency.name};
                });
                pubSub.notify(EVENTS.ON_SECTIONS_UPDATE);
            });
        }
    });
