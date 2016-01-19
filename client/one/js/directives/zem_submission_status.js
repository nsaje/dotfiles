/* globals oneApp, constants */
'use strict';

oneApp.directive('zemSubmissionStatus', function() {
    return {
        restrict: 'E',
        templateUrl: '/partials/zem_submission_status.html',
        scope: {
            statusItems: '=',
            archived: '='
        },
        controller: ['$scope', function($scope) {
            $scope.$watch('statusItems', function(newVal) {
                $scope.approved = $scope.statusItems.filter(function(row) {
                    return row.status === constants.contentAdApprovalStatus.APPROVED;
                });

                $scope.nonApproved = $scope.statusItems.filter(function(row) {
                    return row.status !== constants.contentAdApprovalStatus.APPROVED;
                });

                $scope.zeroStatusItems = $scope.statusItems.length == 0;
            });
        }]
    };
});
