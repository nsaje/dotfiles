/*globals oneApp,moment,constants,options*/
oneApp.controller('AdGroupAdsCtrl', ['$scope', '$state', '$location', '$window', 'api', 'zemCustomTableColsService', function ($scope, $state, $location, $window, api, zemCustomTableColsService) {
    $scope.isSyncRecent = true;
    $scope.selectedArticleIds = [];
    $scope.selectedArticleTotals = true;
    $scope.constants = constants;
    $scope.options = options;
    $scope.chartMetric1 = constants.networkChartMetric.CLICKS;
    $scope.chartMetric2 = constants.networkChartMetric.IMPRESSIONS;
    $scope.dailyStats = [];
    $scope.chartData = undefined;
    $scope.isChartShown = true;
    $scope.chartBtnTitle = 'Hide chart';
    $scope.pagination = {
        currentPage: 1,
        numPages: 5
    };
    $scope.columns = [
        {
            name: 'Cost',
            field: 'cost',
            checked: true,
            type: 'currency'
        },
        {
            name: 'CPC',
            field: 'cpc',
            checked: true,
            type: 'currency'
        },
        {
            name: 'Clicks',
            field: 'clicks',
            checked: true,
            type: 'number'
        },
        {
            name: 'Impressions',
            field: 'impressions',
            checked: true,
            type: 'number'

        },
        {
            name: 'CTR',
            field: 'ctr',
            checked: true,
            type: 'percent'

        }
    ];

    var cols = zemCustomTableColsService.load('adGroupAdsCols', $scope.columns);
    $scope.selectedColumnsCount = cols.length;

    $scope.$watch('columns', function (newValue, oldValue) {
        cols = zemCustomTableColsService.save('adGroupAdsCols', newValue);
        $scope.selectedColumnsCount = cols.length;
    }, true);

    $scope.setChartData = function () {
        var result = {
            formats: [],
            data: [],
            names: []
        };

        result.formats = [$scope.chartMetric1, $scope.chartMetric2].map(function (x) {
            var format = null;
            if (x === constants.networkChartMetric.COST) {
                format = 'currency';
            } else if (x === constants.networkChartMetric.CTR) {
                format = 'percent';
            }

            return format;
        });

        var temp = {};
        $scope.dailyStats.forEach(function (stat) {
            if (!temp.hasOwnProperty(stat.articleId)) {
                temp[stat.articleId] = {
                    name: stat.articleTitle || 'Totals',
                    data: [[]]
                };
            }

            temp[stat.articleId].data[0].push([stat.date, stat[$scope.chartMetric1]]);

            if ($scope.chartMetric2 && $scope.chartMetric2 !== $scope.chartMetric1) {
                if (!temp[stat.articleId].data[1]) {
                    temp[stat.articleId].data[1] = [];
                }
                temp[stat.articleId].data[1].push([stat.date, stat[$scope.chartMetric2]]);
            }
        });

        Object.keys(temp).forEach(function (articleId) {
            result.data.push(temp[articleId].data);
            result.names.push(temp[articleId].name);
        });

        $scope.chartData = result;
    };

    $scope.loadRequestInProgress = false;

    $scope.getTableData = function () {
        $scope.loadRequestInProgress = true;

        api.adGroupAdsTable.get($state.params.id, $scope.pagination.currentPage, $scope.pagination.size, $scope.dateRange.startDate, $scope.dateRange.endDate).then(
            function (data) {
                $scope.rows = data.rows;
                $scope.totals = data.totals;
                $scope.lastSyncDate = data.last_sync ? moment(data.last_sync) : null;
                $scope.isSyncRecent = data.is_sync_recent;

                $scope.pagination = data.pagination;

                $scope.selectArticles();
            },
            function (data) {
                // error
                return;
            }
        ).finally(function () {
            $scope.loadRequestInProgress = false;
        });
    };

    $scope.getDailyStats = function () {
        api.adGroupNetworksDailyStats.list($state.params.id, $scope.dateRange.startDate, $scope.dateRange.endDate, $scope.selectedArticleIds, null, $scope.selectedArticleTotals).then(
            function (data) {
                $scope.dailyStats = data;
                $scope.setChartData();
            },
            function (data) {
                // error
                return;
            }
        );
    };

    $scope.selectedArticlesChanged = function (articleId) {
        var i = 0;
        if (articleId) {
            i = $scope.selectedArticleIds.indexOf(articleId);
            if (i > -1) {
                $scope.selectedArticleIds.splice(i, 1);
            } else {
                $scope.selectedArticleIds.push(articleId);
            }
        }

        if (!$scope.selectedArticleTotals && !$scope.selectedArticleIds.length) {
            $scope.selectedArticleTotals = true;
        }

        $location.search('article_ids', $scope.selectedArticleIds.join(','));
        $location.search('article_totals', $scope.selectedArticleTotals || null);

        $scope.getDailyStats();
    };

    $scope.toggleChart = function () {
        $scope.isChartShown = !$scope.isChartShown;
        $scope.chartBtnTitle = $scope.isChartShown ? 'Hide chart' : 'Show chart';
        $location.search('chart_hidden', !$scope.isChartShown ? '1' : null);
    };

    $scope.$watch('chartMetric1', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.setChartData();
            $location.search('chart_metric1', $scope.chartMetric1);
        }
    });

    $scope.$watch('chartMetric2', function (newValue, oldValue) {
        if (newValue !== oldValue) {
            $scope.setChartData();
            $location.search('chart_metric2', $scope.chartMetric2);
        }
    });

    // From parent scope (mainCtrl).
    $scope.$watch('dateRange', function (newValue, oldValue) {
        $scope.getDailyStats();
        $scope.getTableData();
    });

    $scope.selectArticles = function () {
        $scope.rows.forEach(function (x) {
            if ($scope.selectedArticleIds.indexOf(x.id) > -1) {
                x.checked = true;
            }
        });
    };

    $scope.$on("$stateChangeSuccess", function() {
        var chartMetric1 = $location.search().chart_metric1;
        var chartMetric2 = $location.search().chart_metric2;
        var chartHidden = $location.search().chart_hidden;
        var chartChanged = false;

        if (chartMetric1 !== undefined && $scope.chartMetric1 !== chartMetric1) {
            $scope.chartMetric1 = chartMetric1;
            chartChanged = true;
        }

        if (chartMetric2 !== undefined && $scope.chartMetric2 !== chartMetric2) {
            $scope.chartMetric2 = chartMetric2;
            chartChanged = true;
        }

        if (chartHidden) {
            $scope.isChartShown = false;
        }

        if (chartChanged) {
            $scope.setChartData();
        }

        var page = $location.search().page;
        var size = $location.search().size;
        var articleIds = $location.search().article_ids;
        var articleTotals = $location.search().article_totals;
        var tableChanged = false;

        if (page !== undefined && $scope.pagination.currentPage !== page) {
            $scope.pagination.currentPage = page;
            tableChanged = true;
        }

        if (size !== undefined && $scope.pagination.size !== size) {
            $scope.pagination.size = size;
            tableChanged = true;
        }
        
        if (tableChanged) {
            $scope.loadPage();
        }

        if (articleIds) {
            $scope.selectedArticleIds = articleIds.split(',');

            if ($scope.rows) {
                $scope.selectArticles();
            }
        }

        $scope.selectedArticleTotals = !$scope.selectedArticleIds.length || articleTotals;
    });
    
    // pagination
    $scope.sizeRange = [5, 10, 20, 50];

    $scope.loadPage = function(page) {
        if(page && page > 0 && page <= $scope.pagination.numPages) {
            $scope.pagination.currentPage = page;
        }

        if ($scope.pagination.currentPage && $scope.pagination.size) {
            $location.search('page', $scope.pagination.currentPage);
            $location.search('size', $scope.pagination.size);
            $scope.getTableData();
        }
    };

    // export
    $scope.downloadReport = function() {
        $window.open('api/ad_groups/' + $state.params.id + '/ads/export/?type=' + $scope.exportType + '&start_date=' + $scope.dateRange.startDate.format() + '&end_date=' + $scope.dateRange.endDate.format(), '_blank');
        $scope.exportType = '';
    };
}]);
