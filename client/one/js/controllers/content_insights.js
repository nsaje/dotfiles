/* globals oneApp */
oneApp.controller('ContentInsightsCtrl', ['$scope', '$state', 'api', 'zemNavigationService', function ($scope, $state, api, zemNavigationService) { // eslint-disable-line max-len
    $scope.infoboxLinkTo = 'main.campaigns.settings';
    $scope.summary = 'Titles';
    $scope.metric = 'CTR';
    $scope.rows = [
            {
                summary: 'Test title',
                metric: 10.5,
            },
            {
                summary: 'Test title 2',
                metric: 0.1,
            },
        ];

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

    $scope.init = function () {
        $scope.getInfoboxData();
    };

    $scope.init();
}]);
