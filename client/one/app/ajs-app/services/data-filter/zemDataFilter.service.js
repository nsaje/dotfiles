angular
    .module('one.services')
    .service('zemDataFilterService', function(
        $location,
        zemAuthStore,
        zemPubSubService
    ) {
        // eslint-disable-line max-len
        this.init = init;
        this.getDateRange = getDateRange;
        this.setDateRange = setDateRange;
        this.getAppliedConditions = getAppliedConditions;
        this.getAppliedCondition = getAppliedCondition;
        this.applyConditions = applyConditions;
        this.resetCondition = resetCondition;
        this.resetAllConditions = resetAllConditions;
        this.removeValueFromConditionList = removeValueFromConditionList;
        this.getFilteredSources = getFilteredSources;
        this.getFilteredAgencies = getFilteredAgencies;
        this.getFilteredAccountTypes = getFilteredAccountTypes;
        this.getFilteredBusinesses = getFilteredBusinesses;
        this.getFilteredStatuses = getFilteredStatuses;
        this.getFilteredPublisherStatus = getFilteredPublisherStatus;
        this.getShowArchived = getShowArchived;

        this.onDateRangeUpdate = onDateRangeUpdate;
        this.onDataFilterUpdate = onDataFilterUpdate;
        this.onFilteredSourcesUpdate = onFilteredSourcesUpdate;
        this.onFilteredAgenciesUpdate = onFilteredAgenciesUpdate;
        this.onFilteredAccountTypesUpdate = onFilteredAccountTypesUpdate;
        this.onFilteredStatusesUpdate = onFilteredStatusesUpdate;
        this.onFilteredPublisherStatusUpdate = onFilteredPublisherStatusUpdate;
        this.onFilteredBusinessesUpdate = onFilteredBusinessesUpdate;

        var pubSub = zemPubSubService.createInstance();
        var EVENTS = {
            ON_DATE_RANGE_UPDATE:
                'zem-data-filter-service-on-date-range-update',
            ON_DATA_FILTER_UPDATE:
                'zem-data-filter-service-on-data-filter-update',
            ON_FILTERED_SOURCES_UPDATE:
                'zem-data-filter-service-on-filtered-sources-update',
            ON_FILTERED_AGENCIES_UPDATE:
                'zem-data-filter-service-on-filtered-agencies-update',
            ON_FILTERED_ACCOUNT_TYPES_UPDATE:
                'zem-data-filter-service-on-filtered-account-types-update',
            ON_FILTERED_BUSINESSES_UPDATE:
                'zem-data-filter-service-on-filtered-businesses-update',
            ON_FILTERED_STATUSES_UPDATE:
                'zem-data-filter-service-on-filtered-statuses-update',
            ON_FILTERED_PUBLISHER_STATUS_UPDATE:
                'zem-data-filter-service-on-filtered-publisher-status-update',
        };

        var STATUSES_CONDITION_VALUES = {
            archived: 'archived',
        };
        this.STATUSES_CONDITION_VALUES = STATUSES_CONDITION_VALUES;

        var PUBLISHER_STATUS_CONDITION_VALUES = {
            all: 'all',
            active: 'active',
            blacklisted: 'blacklisted',
        };
        this.PUBLISHER_STATUS_CONDITION_VALUES = PUBLISHER_STATUS_CONDITION_VALUES;

        var CONDITION_TYPES = {
            value: 'value',
            list: 'list',
        };
        this.CONDITION_TYPES = CONDITION_TYPES;

        var CONDITIONS = {
            sources: {
                name: 'sources',
                type: CONDITION_TYPES.list,
                urlParam: 'filtered_sources',
                event: EVENTS.ON_FILTERED_SOURCES_UPDATE,
            },
            agencies: {
                name: 'agencies',
                type: CONDITION_TYPES.list,
                urlParam: 'filtered_agencies',
                event: EVENTS.ON_FILTERED_AGENCIES_UPDATE,
                permissions: ['zemauth.can_filter_by_agency'],
            },
            accountTypes: {
                name: 'accountTypes',
                type: CONDITION_TYPES.list,
                urlParam: 'filtered_account_types',
                event: EVENTS.ON_FILTERED_ACCOUNT_TYPES_UPDATE,
                permissions: ['zemauth.can_filter_by_account_type'],
            },
            businesses: {
                name: 'businesses',
                type: CONDITION_TYPES.list,
                urlParam: 'filtered_businesses',
                event: EVENTS.ON_FILTERED_BUSINESSES_UPDATE,
                permissions: ['zemauth.can_filter_by_business'],
            },
            statuses: {
                name: 'statuses',
                type: CONDITION_TYPES.list,
                urlParam: 'filtered_statuses',
                event: EVENTS.ON_FILTERED_STATUSES_UPDATE,
            },
            publisherStatus: {
                name: 'publisherStatus',
                type: CONDITION_TYPES.value,
                urlParam: 'filtered_publisher_status',
                default: PUBLISHER_STATUS_CONDITION_VALUES.all,
                event: EVENTS.ON_FILTERED_PUBLISHER_STATUS_UPDATE,
                permissions: ['zemauth.can_see_publishers'],
            },
        };
        this.CONDITIONS = CONDITIONS;

        var dateRange = {startDate: null, endDate: null};
        var appliedConditions = {};

        //
        // Public methods
        //
        function init() {
            dateRange = {
                startDate: moment().startOf('month'),
                endDate: moment().endOf('month'),
            };

            // Set conditions default values and update them with url params
            angular.forEach(CONDITIONS, function(condition) {
                if (angular.isDefined(condition.default)) {
                    appliedConditions[condition.name] = condition.default;
                }
            });
        }

        function getDateRange() {
            return angular.copy(dateRange);
        }

        function setDateRange(newDateRange) {
            var updated = false;

            if (
                newDateRange.startDate &&
                newDateRange.startDate.isValid() &&
                !newDateRange.startDate.isSame(dateRange.startDate)
            ) {
                dateRange.startDate = newDateRange.startDate;
                updated = true;
            }

            if (
                newDateRange.endDate &&
                newDateRange.endDate.isValid() &&
                !newDateRange.endDate.isSame(dateRange.endDate)
            ) {
                dateRange.endDate = newDateRange.endDate;
                updated = true;
            }

            var formattedStartDate = dateRange.startDate.format('YYYY-MM-DD');
            if (
                formattedStartDate !==
                moment()
                    .startOf('month')
                    .format('YYYY-MM-DD')
            ) {
                setUrlParam('start_date', formattedStartDate);
            } else {
                setUrlParam('start_date', null);
            }

            var formattedEndDate = dateRange.endDate.format('YYYY-MM-DD');
            if (
                formattedEndDate !==
                moment()
                    .endOf('month')
                    .format('YYYY-MM-DD')
            ) {
                setUrlParam('end_date', formattedEndDate);
            } else {
                setUrlParam('end_date', null);
            }

            if (updated) {
                pubSub.notify(EVENTS.ON_DATE_RANGE_UPDATE);
            }
        }

        function getAppliedConditions() {
            return angular.copy(appliedConditions);
        }

        function getAppliedCondition(condition) {
            if (!condition) return;

            switch (condition.type) {
                case CONDITION_TYPES.value:
                    return getAppliedConditions()[condition.name] || null;
                case CONDITION_TYPES.list:
                    return getAppliedConditions()[condition.name] || [];
            }
        }

        function applyConditions(conditions) {
            var updated = false;
            angular.forEach(conditions, function(condition) {
                updated =
                    setCondition(condition.condition, condition.value) ||
                    updated;
            });
            if (updated) {
                pubSub.notify(EVENTS.ON_DATA_FILTER_UPDATE);
            }
        }

        function resetAllConditions() {
            var updated = false;
            var ignoreNotify = true;
            angular.forEach(CONDITIONS, function(condition) {
                updated = resetCondition(condition, ignoreNotify) || updated;
            });
            if (updated) {
                pubSub.notify(EVENTS.ON_DATA_FILTER_UPDATE);
            }
        }

        function resetCondition(condition, ignoreNotify) {
            if (!condition) return;

            var updated = false;
            switch (condition.type) {
                case CONDITION_TYPES.value:
                    updated = setCondition(
                        condition,
                        condition.default || null
                    );
                    break;
                case CONDITION_TYPES.list:
                    updated = setCondition(condition, condition.default || []);
                    break;
            }

            if (updated && !ignoreNotify) {
                pubSub.notify(EVENTS.ON_DATA_FILTER_UPDATE);
            }

            return updated;
        }

        function removeValueFromConditionList(condition, value, ignoreNotify) {
            var values = getAppliedCondition(condition);
            if (!values) return;

            var index = values.indexOf(value);
            if (index !== -1) {
                values.splice(index, 1);
                setCondition(condition, values);
            }

            if (!ignoreNotify) {
                pubSub.notify(EVENTS.ON_DATA_FILTER_UPDATE);
            }
        }

        function getFilteredSources() {
            return getAppliedCondition(CONDITIONS.sources);
        }

        function getFilteredAgencies() {
            return getAppliedCondition(CONDITIONS.agencies);
        }

        function getFilteredAccountTypes() {
            return getAppliedCondition(CONDITIONS.accountTypes);
        }

        function getFilteredBusinesses() {
            return getAppliedCondition(CONDITIONS.businesses);
        }

        function getFilteredStatuses() {
            return getAppliedCondition(CONDITIONS.statuses);
        }

        function getFilteredPublisherStatus() {
            return getAppliedCondition(CONDITIONS.publisherStatus);
        }

        function getShowArchived() {
            return (
                getAppliedCondition(CONDITIONS.statuses).indexOf(
                    STATUSES_CONDITION_VALUES.archived
                ) !== -1
            );
        }

        //
        // Events
        //
        function onDateRangeUpdate(callback) {
            return pubSub.register(EVENTS.ON_DATE_RANGE_UPDATE, callback);
        }

        function onDataFilterUpdate(callback) {
            return pubSub.register(EVENTS.ON_DATA_FILTER_UPDATE, callback);
        }

        function onFilteredSourcesUpdate(callback) {
            return pubSub.register(EVENTS.ON_FILTERED_SOURCES_UPDATE, callback);
        }

        function onFilteredAgenciesUpdate(callback) {
            return pubSub.register(
                EVENTS.ON_FILTERED_AGENCIES_UPDATE,
                callback
            );
        }

        function onFilteredAccountTypesUpdate(callback) {
            return pubSub.register(
                EVENTS.ON_FILTERED_ACCOUNT_TYPES_UPDATE,
                callback
            );
        }

        function onFilteredStatusesUpdate(callback) {
            return pubSub.register(
                EVENTS.ON_FILTERED_STATUSES_UPDATE,
                callback
            );
        }

        function onFilteredPublisherStatusUpdate(callback) {
            return pubSub.register(
                EVENTS.ON_FILTERED_PUBLISHER_STATUS_UPDATE,
                callback
            );
        }

        function onFilteredBusinessesUpdate(callback) {
            return pubSub.register(
                EVENTS.ON_FILTERED_PUBLISHER_STATUS_UPDATE,
                callback
            );
        }

        //
        // Private methods
        //

        function setUrlParam(name, value) {
            if (!value) value = null;
            $location.search(name, value).replace();
        }

        function setCondition(condition, value) {
            var updated = false;
            switch (condition.type) {
                case CONDITION_TYPES.value:
                    updated = setConditionValue(condition, value);
                    break;
                case CONDITION_TYPES.list:
                    var list = angular.isArray(value)
                        ? value
                        : value.split(',');
                    updated = setConditionList(condition, list);
                    break;
            }
            return updated;
        }

        function setConditionValue(condition, value) {
            if (condition.type !== CONDITION_TYPES.value) return false;
            if (
                condition.permissions &&
                !zemAuthStore.hasPermission(condition.permissions)
            ) {
                return false;
            }
            if (angular.equals(getAppliedCondition(condition), value))
                return false;

            appliedConditions[condition.name] = value;
            setUrlParam(condition.urlParam, value);
            pubSub.notify(condition.event, getAppliedCondition(condition));
            return true;
        }

        function setConditionList(condition, list) {
            if (condition.type !== CONDITION_TYPES.list) return false;
            if (
                condition.permissions &&
                !zemAuthStore.hasPermission(condition.permissions)
            ) {
                return false;
            }
            if (angular.equals(getAppliedCondition(condition), list))
                return false;
            appliedConditions[condition.name] = list;
            setUrlParam(condition.urlParam, list.join(','));
            pubSub.notify(condition.event, getAppliedCondition(condition));
            return true;
        }
    });
