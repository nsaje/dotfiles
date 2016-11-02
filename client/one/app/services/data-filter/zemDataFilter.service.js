angular.module('one.services').service('zemDataFilterService', ['$location', 'zemPermissions', 'zemPubSubService', function ($location, zemPermissions, zemPubSubService) { // eslint-disable-line max-len
    this.init = init;
    this.getDateRange = getDateRange;
    this.setDateRange = setDateRange;
    this.getAppliedConditions = getAppliedConditions;
    this.getAppliedCondition = getAppliedCondition;
    this.applyConditions = applyConditions;
    this.resetCondition = resetCondition;
    this.resetAllConditions = resetAllConditions;
    this.removeValueFromConditionList = removeValueFromConditionList;
    this.getShowArchived = getShowArchived;

    this.onDateRangeUpdate = onDateRangeUpdate;
    this.onAppliedConditionsUpdate = onAppliedConditionsUpdate;
    this.onFilteredSourcesUpdate = onFilteredSourcesUpdate;
    this.onFilteredAgenciesUpdate = onFilteredAgenciesUpdate;
    this.onFilteredAccountTypesUpdate = onFilteredAccountTypesUpdate;
    this.onFilteredStatusesUpdate = onFilteredStatusesUpdate;
    this.onFilteredPublisherStatusUpdate = onFilteredPublisherStatusUpdate;


    var pubSub = zemPubSubService.createInstance();
    var EVENTS = {
        ON_DATE_RANGE_UPDATE: 'zem-data-filter-service-on-date-range-update',
        ON_APPLIED_CONDITIONS_UPDATE: 'zem-data-filter-service-on-applied-conditions-update',
        ON_FILTERED_SOURCES_UPDATE: 'zem-data-filter-service-on-filtered-sources-update',
        ON_FILTERED_AGENCIES_UPDATE: 'zem-data-filter-service-on-filtered-agencies-update',
        ON_FILTERED_ACCOUNT_TYPES_UPDATE: 'zem-data-filter-service-on-filtered-account-types-update',
        ON_FILTERED_STATUSES_UPDATE: 'zem-data-filter-service-on-filtered-statuses-update',
        ON_FILTERED_PUBLISHER_STATUS_UPDATE: 'zem-data-filter-service-on-filtered-publisher-status-update',
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
    function init () {
        dateRange = {
            startDate: moment().subtract(29, 'day').startOf('day'),
            endDate: moment().subtract(1, 'day').endOf('day'),
        };

        // Set conditions default values and update them with url params
        angular.forEach(CONDITIONS, function (condition) {
            if (angular.isDefined(condition.default)) {
                appliedConditions[condition.name] = condition.default;
            }
        });
        initFilterFromUrlParams();
    }

    function getDateRange () {
        return angular.copy(dateRange);
    }

    function setDateRange (newDateRange) {
        var updated = false;

        if (newDateRange.startDate.isValid() && !newDateRange.startDate.isSame(dateRange.startDate)) {
            dateRange.startDate = newDateRange.startDate;
            updated = true;
        }

        if (newDateRange.endDate.isValid() && !newDateRange.endDate.isSame(dateRange.endDate)) {
            dateRange.endDate = newDateRange.endDate;
            updated = true;
        }

        if (updated) {
            pubSub.notify(EVENTS.ON_DATE_RANGE_UPDATE, getDateRange());
            setUrlParam('start_date', dateRange.startDate.format('YYYY-MM-DD'));
            setUrlParam('end_date', dateRange.endDate.format('YYYY-MM-DD'));
        }
    }

    function getAppliedConditions () {
        return angular.copy(appliedConditions);
    }

    function getAppliedCondition (condition) {
        if (!condition) return;

        switch (condition.type) {
        case CONDITION_TYPES.value:
            return getAppliedConditions()[condition.name] || null;
        case CONDITION_TYPES.list:
            return getAppliedConditions()[condition.name] || [];
        }
    }

    function applyConditions (conditions) {
        angular.forEach(conditions, function (condition) {
            setCondition(condition.condition, condition.value);
        });
        pubSub.notify(EVENTS.ON_APPLIED_CONDITIONS_UPDATE, getAppliedConditions());
    }

    function resetCondition (condition) {
        if (!condition) return;

        switch (condition.type) {
        case CONDITION_TYPES.value:
            setCondition(condition, condition.default || null);
            break;
        case CONDITION_TYPES.list:
            setCondition(condition, condition.default || []);
            break;
        }
        pubSub.notify(EVENTS.ON_APPLIED_CONDITIONS_UPDATE, getAppliedConditions());
    }

    function resetAllConditions () {
        angular.forEach(CONDITIONS, function (condition) {
            resetCondition(condition);
        });
        pubSub.notify(EVENTS.ON_APPLIED_CONDITIONS_UPDATE, getAppliedConditions());
    }

    function removeValueFromConditionList (condition, value) {
        var values = getAppliedCondition(condition);
        if (!values) return;

        var index = values.indexOf(value);
        if (index !== -1) {
            values.splice(index, 1);
            setCondition(condition, values);
        }
        pubSub.notify(EVENTS.ON_APPLIED_CONDITIONS_UPDATE, getAppliedConditions());
    }

    function getShowArchived () {
        return getAppliedCondition(CONDITIONS.statuses).indexOf(STATUSES_CONDITION_VALUES.archived) !== -1;
    }


    //
    // Events
    //
    function onDateRangeUpdate (callback) {
        return pubSub.register(EVENTS.ON_DATE_RANGE_UPDATE, callback);
    }

    function onAppliedConditionsUpdate (callback) {
        return pubSub.register(EVENTS.ON_APPLIED_CONDITIONS_UPDATE, callback);
    }

    function onFilteredSourcesUpdate (callback) {
        return pubSub.register(EVENTS.ON_FILTERED_SOURCES_UPDATE, callback);
    }

    function onFilteredAgenciesUpdate (callback) {
        return pubSub.register(EVENTS.ON_FILTERED_AGENCIES_UPDATE, callback);
    }

    function onFilteredAccountTypesUpdate (callback) {
        return pubSub.register(EVENTS.ON_FILTERED_ACCOUNT_TYPES_UPDATE, callback);
    }

    function onFilteredStatusesUpdate (callback) {
        return pubSub.register(EVENTS.ON_FILTERED_STATUSES_UPDATE, callback);
    }

    function onFilteredPublisherStatusUpdate (callback) {
        return pubSub.register(EVENTS.ON_FILTERED_PUBLISHER_STATUS_UPDATE, callback);
    }


    //
    // Private methods
    //
    function initFilterFromUrlParams () {
        var params = $location.search();

        // Date range
        var startDateParam = params.start_date;
        var endDateParam = params.end_date;
        if (startDateParam) dateRange.startDate = moment(startDateParam);
        if (endDateParam) dateRange.endDate = moment(endDateParam);

        // Conditions
        angular.forEach(CONDITIONS, function (condition) {
            var param = params[condition.urlParam];
            if (param) {
                setCondition(condition, param);
            }
        });
    }

    function setUrlParam (name, value) {
        if (!value) value = null;
        $location.search(name, value);
    }

    function setCondition (condition, value) {
        switch (condition.type) {
        case CONDITION_TYPES.value:
            setConditionValue(condition, value);
            break;
        case CONDITION_TYPES.list:
            var list = angular.isArray(value) ? value : value.split(',');
            setConditionList(condition, list);
            break;
        }
    }

    function setConditionValue (condition, value) {
        if (condition.type !== CONDITION_TYPES.value) return;
        if (condition.permissions && !zemPermissions.hasPermission(condition.permissions)) return;

        if (appliedConditions[condition.name] !== value) {
            appliedConditions[condition.name] = value;
            setUrlParam(condition.urlParam, value);
            pubSub.notify(condition.event, getAppliedCondition(condition));
        }
    }

    function setConditionList (condition, list) {
        if (condition.type !== CONDITION_TYPES.list) return;
        if (condition.permissions && !zemPermissions.hasPermission(condition.permissions)) return;

        if (appliedConditions[condition.name] !== list) {
            appliedConditions[condition.name] = list;
            setUrlParam(condition.urlParam, list.join(','));
            pubSub.notify(condition.event, getAppliedCondition(condition));
        }
    }
}]);
