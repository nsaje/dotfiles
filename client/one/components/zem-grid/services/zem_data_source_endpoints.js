/* globals oneApp, angular */
'use strict';

oneApp.factory('zemDataSourceEndpoints', ['$rootScope', '$controller', '$http', '$q', function ($rootScope, $controller, $http, $q) { // eslint-disable-line max-len

    function StatsEndpoint (baseUrl, metaData) {
        this.metaData = metaData;
        this.baseUrl = baseUrl;

        this.getMetaData = function () {
            // Meta data is not yet fetched from backend,
            // therefor just return already fulfilled promise
            var deferred = $q.defer();
            deferred.resolve(this.metaData);
            return deferred.promise;
        };

        this.getData = function (config) {
            var url = createUrl(baseUrl, config);
            convertToApi(config);
            var deferred = $q.defer();
            $http.post(url, {params: config}).success(function (data) {
                var breakdowns = data.data;
                breakdowns.forEach(function (breakdown) {
                    convertFromApi(config, breakdown);
                    checkPaginationCount(config, breakdown);
                });
                deferred.resolve(breakdowns);
            }).error(function (data) {
                deferred.reject(data);
            });

            return deferred.promise;
        };

        function createUrl (baseUrl, config) {
            var queries = config.breakdown.map(function (breakdown) {
                return breakdown.query;
            });
            return baseUrl + queries.join('/') + '/';
        }

        function convertFromApi (config, breakdown) {
            breakdown.level = config.level;
            breakdown.breakdownId = breakdown.breakdown_id;
            breakdown.rows = breakdown.rows.map(function (row) {
                row.breakdownName = row.breakdown_name;
                return {
                    stats: row,
                    breakdownId: row.breakdown_id,
                };
            });
        }

        function convertToApi (config) {
            config.breakdown_page = config.breakdownPage; // eslint-disable-line camelcase
            config.start_date = config.startDate.format('YYYY-MM-DD'); // eslint-disable-line camelcase
            config.end_date = config.endDate.format('YYYY-MM-DD'); // eslint-disable-line camelcase
            delete config.breakdownPage;
            delete config.breakdown;
        }

        function checkPaginationCount (config, breakdown) {
            // In case that pagination.count is not provided,
            // we can check if returned data size is less then
            // requested one -- in that case set the count to
            // the current size od data
            var pagination = breakdown.pagination;
            if (pagination.count < 0) {
                if (config.limit > pagination.limit) {
                    pagination.count = pagination.offset + pagination.limit;
                }
            }
        }

        function saveData (value, row, column) {

            // Use endpoint for save

            // function AdGroupContentAdState ()
            //      this.save = function (adGroupId, state, contentAdIdsSelected, contentAdIdsNotSelected, selectedAll, selectedBatch) {

            //function AdGroupSettings () {
            //    this.save = function (settings) { // settings = {adgroup: id, field: value}

            //function AdGroupSourceSettings () {
            //    this.save = function (adGroupId, sourceId, data) {


            // Settings
            //      -> id + {field:value}
            // State
            //      -> AdGroup State --> id, {state: value} --> url + data
            //      -> AdGroupSource State --> id, sourceid, state --> url + data
            //      -> ContentAd State --> id, state, [contentAds]

            // ID -> Endpoint arg
            // Field: Value - param column
            // Value - new value
            //
            var id = $state.id;
            column.onSave(id, );

        }
    }


    //
    // TODO: Dedicated service for breakdowns and columns definitions
    //
    var BREAKDOWN_GROUPS = [
        {
            name: 'Base level',
            breakdowns: [
                // Base level breakdown - defined later based on Endpoint type
            ],
        },
        {
            name: 'By delivery',
            breakdowns: [
                {name: 'Age', query: 'age'},
                {name: 'Gender', query: 'gender'},
                {name: 'Age and Gender', query: 'agegender'},
                {name: 'Country', query: 'country'},
                {name: 'State', query: 'state'},
                {name: 'DMA', query: 'dma'},
                {name: 'Device', query: 'device'},
            ],
        },
        {
            name: 'By structure',
            breakdowns: [
                // Type specific structure breakdown - Defined later based on Endpoint type
                {name: 'By media source', query: 'source'},
                {name: 'By publishers', query: 'publishers'},
            ],
        },
        {
            name: 'By time',
            breakdowns: [
                {name: 'By day', query: 'day'},
                {name: 'By week', query: 'week'},
                {name: 'By month', query: 'month'},
            ],
        },
    ];

    var BASE_LEVEL_BREAKDOWNS = [
        {name: 'By Account', query: 'account'},
        {name: 'By Campaign', query: 'campaign'},
        {name: 'By Ad Group', query: 'adgroup'},
    ];

    var STRUCTURE_LEVEL_BREAKDOWNS = [
        {name: 'By Campaign', query: 'campaign'},
        {name: 'By Ad Group', query: 'adgroup'},
        {name: 'By Content Ad', query: 'contentad'},
    ];

    function getControllerMetaData (scope, ctrl) {
        //
        // HACK (legacy support): access columns variable from corresponded controller scope
        //
        try { $controller(ctrl, {$scope: scope}); } catch (e) { } // eslint-disable-line

        // Replace first column type to text and field breakdown name, to solve
        // temporary problems with primary column content in level>1 breakdowns
        // FIXME: find appropriate solution for this problem (special type)
        scope.columns[0].field = 'breakdownName';
        scope.columns[0].type = 'text';

        // Types not supported atm, therefor just assume Account type,
        // and add required base and structure level breakdowns
        var breakdownGroups = angular.copy(BREAKDOWN_GROUPS);
        breakdownGroups[0].breakdowns.push(BASE_LEVEL_BREAKDOWNS[0]);
        breakdownGroups[2].breakdowns.unshift(STRUCTURE_LEVEL_BREAKDOWNS[0]);

        return {
            columns: scope.columns,
            categories: scope.columnCategories,
            breakdownGroups: breakdownGroups,
            localStoragePrefix: scope.localStoragePrefix,
        };
    }

    return {
        createAllAccountsEndpoint: function (metaData) {
            return new StatsEndpoint('/api/all_accounts/breakdown/', metaData);
        },
        getControllerMetaData: getControllerMetaData,
    };
}]);
