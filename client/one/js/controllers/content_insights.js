/* globals oneApp */
oneApp.controller('ContentInsightsCtrl', ['$scope', '$state', 'api', 'zemNavigationService', function ($scope, $state, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.infoboxLinkTo = 'main.campaigns.settings';
    $scope.summary = 'Titles';
    $scope.metric = 'CTR';
    $scope.rows = [];

    $scope.getInfoboxData = function () {
        api.campaignOverview.get(
            $state.params.id,
            $scope.dateRange.startDate,
            $scope.dateRange.endDate
        ).then(
            function (data) {
                $scope.infoboxHeader = data.header;
                $scope.infoboxBasicSettings = data.basicSettings;
                $scope.infoboxPerformanceSettings = data.performanceSettings;
                $scope.reflowGraph(1);
            }
        );
    };

    $scope.getContentInsights = function () {
        api.campaignContentInsights.get(
            $state.params.id,
            $scope.dateRange.startDate,
            $scope.dateRange.endDate
        ).then(
            function (data) {
                $scope.summary = data.summary;
                $scope.metric = data.metric;
                $scope.rows = data.rows;
            }
        );
    };

    $scope.init = function () {
        $scope.getInfoboxData();
        $scope.getContentInsights();
    };

    $scope.init();
}]);
