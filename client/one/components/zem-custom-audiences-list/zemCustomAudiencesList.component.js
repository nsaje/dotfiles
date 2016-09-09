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

angular.module('one.legacy').controller('ZemCustomAudiencesListCtrl', ['api', function (api) {
    var vm = this;
    vm.audiences = [];
    vm.listRequestInProgress = false;

    vm.getAudiences = function () {
        vm.listRequestInProgress = true;

        api.customAudiences.list(vm.accountId).then(
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

    function init () {
        vm.getAudiences();
    }

    init();
}]);
