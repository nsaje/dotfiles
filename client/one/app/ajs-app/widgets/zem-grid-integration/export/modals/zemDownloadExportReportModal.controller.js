var routerHelpers = require('../../../../../shared/helpers/router.helpers');

//
// TODO: On major update, refactor to component
//
angular
    .module('one.widgets')
    .controller('zemDownloadExportReportModalCtrl', function(
        $scope,
        $window,
        NgRouter,
        zemDataFilterService,
        zemDownloadExportReportModalEndpoint
    ) {
        // eslint-disable-line max-len
        $scope.showInProgress = false;
        $scope.export = {};

        $scope.setDisabledExportOptions = function() {
            $scope.showInProgress = true;
            var dateRange = zemDataFilterService.getDateRange();
            var activatedRoute = routerHelpers.getActivatedRoute(NgRouter);
            zemDownloadExportReportModalEndpoint
                .get(
                    activatedRoute.snapshot.paramMap.get('id'),
                    $scope.level,
                    $scope.exportSources,
                    dateRange.startDate,
                    dateRange.endDate
                )
                .then(function(data) {
                    $scope.options.forEach(function(opt) {
                        if (opt.value === constants.exportType.CONTENT_AD) {
                            opt.disabled = !data.content_ad;
                            opt.disabledByDay = !data.byDay.content_ad;
                        } else if (
                            opt.value === constants.exportType.AD_GROUP
                        ) {
                            opt.disabled = !data.ad_group;
                            opt.disabledByDay = !data.byDay.ad_group;
                        } else if (
                            opt.value === constants.exportType.CAMPAIGN
                        ) {
                            opt.disabled = !data.campaign;
                            opt.disabledByDay = !data.byDay.campaign;
                        } else if (opt.value === constants.exportType.ACCOUNT) {
                            opt.disabled = !data.account;
                            opt.disabledByDay = !data.byDay.account;
                        } else if (
                            opt.value === constants.exportType.ALL_ACCOUNTS
                        ) {
                            opt.disabled = !data.all_accounts;
                            opt.disabledByDay = !data.byDay.all_accounts;
                        }
                    });
                })
                .finally(function() {
                    $scope.checkDownloadAllowed();
                    $scope.showInProgress = false;
                });
        };

        $scope.checkDownloadAllowed = function() {
            var option = getOptionByValue($scope.export.type.value);
            $scope.downloadAllowed = true;
            $scope.downloadNotAllowedMessage = '';

            if (option.disabledByDay && $scope.export.byDay) {
                $scope.downloadNotAllowedMessage =
                    'Please select shorter date range to download report ' +
                    'with breakdown by day.';
                $scope.downloadAllowed = false;
            }
            if (option.disabled) {
                $scope.downloadNotAllowedMessage =
                    'This report is not available for download due to the ' +
                    'volume of content. Please select shorter date range or different granularity.';
                $scope.downloadAllowed = false;
            }
        };

        $scope.downloadReport = function() {
            var dateRange = zemDataFilterService.getDateRange();
            var url =
                $scope.baseUrl +
                'export/?type=' +
                $scope.export.type.value +
                '&start_date=' +
                dateRange.startDate.format() +
                '&end_date=' +
                dateRange.endDate.format() +
                '&order=' +
                $scope.order +
                '&by_day=' +
                $scope.export.byDay;

            url += '&include_missing=' + $scope.export.includeMissing;
            url += '&include_model_ids=' + $scope.export.includeIds;
            url += '&include_totals=' + $scope.export.includeTotals;

            var filteredSources = zemDataFilterService.getFilteredSources();
            var filteredAgencies = zemDataFilterService.getFilteredAgencies();
            var filteredAccountTypes = zemDataFilterService.getFilteredAccountTypes();
            if (filteredSources.length > 0) {
                url += '&filtered_sources=' + filteredSources.join(',');
            }
            if (filteredAgencies.length > 0) {
                url += '&filtered_agencies=' + filteredAgencies.join(',');
            }
            if (filteredAccountTypes.length > 0) {
                url +=
                    '&filtered_account_types=' + filteredAccountTypes.join(',');
            }

            url +=
                '&additional_fields=' + $scope.getAdditionalColumns().join(',');
            $window.open(url, '_blank');
            $scope.$close();
        };

        $scope.init = function() {
            $scope.export.type = $scope.defaultOption;
            $scope.setDisabledExportOptions();
        };
        $scope.init();

        function getOptionByValue(value) {
            var option = null;
            $scope.options.forEach(function(opt) {
                if (opt.value === value) {
                    option = opt;
                }
            });
            return option;
        }
    });

angular
    .module('one.widgets')
    .service('zemDownloadExportReportModalEndpoint', function(
        $q,
        $http,
        zemDataFilterService
    ) {
        // eslint-disable-line max-len

        this.get = get;

        function get(id_, level_, exportSources, startDate, endDate) {
            var deferred = $q.defer();

            var filteredSources = zemDataFilterService.getFilteredSources();
            var urlId =
                level_ === constants.level.ALL_ACCOUNTS ? '' : id_ + '/';
            var urlSources = exportSources.valueOf() ? 'sources/' : '';
            var urlFilteredSources = exportSources.valueOf()
                ? '?filtered_sources=' + filteredSources.join(',')
                : '';
            var url =
                '/api/' +
                level_ +
                '/' +
                urlId +
                urlSources +
                'export/allowed/' +
                urlFilteredSources;

            var config = {
                params: {},
            };
            if (startDate) {
                config.params.start_date = startDate.format();
            }
            if (endDate) {
                config.params.end_date = endDate.format();
            }
            addAgencyFilter(config.params);
            addAccountTypeFilter(config.params);

            $http
                .get(url, config)
                .success(function(data) {
                    var resource;

                    if (data && data.data) {
                        resource = convertFromApi(data.data);
                    }

                    deferred.resolve(resource);
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        function addAgencyFilter(params) {
            var filteredAgencies = zemDataFilterService.getFilteredAgencies();
            if (filteredAgencies.length > 0) {
                params.filtered_agencies = filteredAgencies;
            }
        }
        function addAccountTypeFilter(params) {
            var filteredAccountTypes = zemDataFilterService.getFilteredAccountTypes();
            if (filteredAccountTypes.length > 0) {
                params.filtered_account_types = filteredAccountTypes;
            }
        }
        function convertFromApi(data) {
            return {
                content_ad: data.content_ad,
                ad_group: data.ad_group,
                campaign: data.campaign,
                account: data.account,
                all_accounts: data.all_accounts,
                byDay: {
                    content_ad: data.by_day.content_ad,
                    ad_group: data.by_day.ad_group,
                    campaign: data.by_day.campaign,
                    account: data.by_day.account,
                    all_accounts: data.by_day.all_accounts,
                },
            };
        }
    });
