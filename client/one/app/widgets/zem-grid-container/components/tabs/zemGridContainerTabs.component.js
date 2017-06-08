angular.module('one.widgets').component('zemGridContainerTabs', {
    templateUrl: '/app/widgets/zem-grid-container/components/tabs/zemGridContainerTabs.component.html',
    bindings: {
        tabs: '<',
        entity: '<',
    },
    controller: function ($rootScope, $state, $location, $window, zemUtils) {
        var $ctrl = this;

        $ctrl.navigateTo = navigateTo;

        $ctrl.$onInit = function () {
        };

        function navigateTo (event, option) {
            var id = $ctrl.entity ? $ctrl.entity.id : null;
            var level = $ctrl.entity ? constants.entityTypeToLevelMap[$ctrl.entity.type] : constants.level.ALL_ACCOUNTS;
            var levelStateParam = constants.levelToLevelStateParamMap[level];
            var breakdownStateParam = constants.breakdownToBreakdownStateParamMap[option.breakdown];
            var params = {
                id: id,
                level: levelStateParam,
                breakdown: breakdownStateParam
            };

            if (zemUtils.shouldOpenInNewTab(event)) {
                $window.open(getStateHrefWithQueryParams(params), '_blank');
            } else {
                // [WORKAROUND] Silently change state (notify: false) to avoid component reinitialization
                // and notify directly with $zemStateChangeStart and $zemStateChangeSuccess
                $rootScope.$broadcast('$zemStateChangeStart');
                $state.go('v2.analytics', params, {notify: false, location: 'replace'}).then(function () {
                    $rootScope.$broadcast('$zemStateChangeSuccess');
                });
            }
        }

        function getStateHrefWithQueryParams (params) {
            var href = $state.href('v2.analytics', params);
            var queryParamsIndex = $location.url().indexOf('?');
            if (queryParamsIndex !== -1) {
                href += $location.url().slice(queryParamsIndex);
            }
            return href;
        }
    }
});

