/*globals angular*/
'use strict';

angular.module('one.legacy').directive('zemCustomAudiencesList', [function () { // eslint-disable-line max-len
    return {
        restrict: 'E',
        replace: true,
        scope: {},
        templateUrl: '/components/zem-custom-audiences-list/zemCustomAudiencesList.component.html',
        bindToController: {
            accountId: '=',
        },
        controllerAs: 'ctrl',
        controller: 'ZemCustomAudiencesListCtrl',
    };
}]);

angular.module('one.legacy').controller('ZemCustomAudiencesListCtrl', ['api', 'zemFilterService', '$scope', function (api, zemFilterService, $scope) {
    var vm = this;
    vm.audiences = [];
    vm.listRequestInProgress = false;
    vm.archiveRequestInProgress = {};
    vm.restoreRequestInProgress = {};

    vm.archiveAudience = function (audienceId) {
        vm.archiveRequestInProgress[audienceId] = true;

        api.customAudiencesArchive.archive(vm.accountId, audienceId).then(
            function (data) {
                for (var i = 0; i < vm.audiences.length; i++) {
                    if (vm.audiences[i].id === audienceId) {
                        vm.audiences[i].archived = true;
                    }
                }
            },
            function (data) {
                return;
            }
        ).finally(function () {
            delete vm.archiveRequestInProgress[audienceId];
        });
    };

    vm.restoreAudience = function (audienceId) {
        vm.restoreRequestInProgress[audienceId] = true;

        api.customAudiencesArchive.restore(vm.accountId, audienceId).then(
            function (data) {
                for (var i = 0; i < vm.audiences.length; i++) {
                    if (vm.audiences[i].id === audienceId) {
                        vm.audiences[i].archived = false;
                    }
                }
            },
            function (data) {
                return;
            }
        ).finally(function () {
            delete vm.restoreRequestInProgress[audienceId];
        });
    };

    vm.getAudiences = function () {
        vm.listRequestInProgress = true;

        api.customAudiences.list(vm.accountId, zemFilterService.getShowArchived()).then(
            function (data) {
                vm.audiences = data;
            },
            function (data) {
                return;
            }
        ).finally(function () {
            vm.listRequestInProgress = false;
        });
    };

    $scope.$watch(zemFilterService.getShowArchived, function (newValue, oldValue) {
        if (angular.equals(newValue, oldValue)) {
            return;
        }

        vm.getAudiences();
    }, true);

    function init () {
        vm.getAudiences();
    }

    init();
}]);
