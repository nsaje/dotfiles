/* global oneApp,constants */
'use strict';

oneApp.directive('zemIconList', [function () {
    var statusIcons = {},
        statusClasses = {};
    statusIcons[constants.emoticon.HAPPY] = 'happy_face.svg';
    statusClasses[constants.emoticon.HAPPY] = 'img-icon-happy';
    statusIcons[constants.emoticon.SAD] = 'sad_face.svg';
    statusClasses[constants.emoticon.SAD] = 'img-icon-sad';
    statusIcons[constants.emoticon.NEUTRAL] = 'neutral_face.svg';
    statusClasses[constants.emoticon.NEUTRAL] = 'img-icon-neutral';
    return {
        restrict: 'E',
        scope: {
            'statuses': '=statuses',
        },
        templateUrl: '/partials/zem_icon_list.html',
        controller: ['$scope', function ($scope) {
            $scope.popover = '<ul class="icon-list">';
            if (!$scope.statuses) {
                return;
            }
            $scope.iconFile = '';
            $scope.statusList = [];
            if ($scope.statuses.overall !== undefined) {
                $scope.iconFile = statusIcons[$scope.statuses.overall];
                $scope.iconClass = statusClasses[$scope.statuses.overall];
            }
            ($scope.statuses.list || []).forEach(function (status) {
                var file = statusIcons[status.emoticon],
                    cls = statusIcons[status.emoticon];
                $scope.popover += '<li>';
                $scope.popover += '<zem-icon file="' + file + '" img-class="' + cls + '"></zem-icon> ';
                $scope.popover += status.text;
                $scope.popover += '</li>';
            });
            $scope.popover += '</ul>';
        }],
    };

}]);
