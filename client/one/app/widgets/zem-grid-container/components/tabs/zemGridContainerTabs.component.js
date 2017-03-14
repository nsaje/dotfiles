angular.module('one.widgets').component('zemGridContainerTabs', {
    templateUrl: '/app/widgets/zem-grid-container/components/tabs/zemGridContainerTabs.component.html',
    bindings: {
        tabs: '<',
        entity: '<',
    },
    controller: function ($rootScope, $state) {
        var $ctrl = this;

        $ctrl.navigateTo = navigateTo;

        $ctrl.$onInit = function () {
        };

        function navigateTo (option) {
            var id = $ctrl.entity ? $ctrl.entity.id : null;
            var level = $ctrl.entity ? constants.entityTypeToLevelMap[$ctrl.entity.type] : constants.level.ALL_ACCOUNTS;
            var levelStateParam = constants.levelToLevelStateParamMap[level];
            var breakdownStateParam = constants.breakdownToBreakdownStateParamMap[option.breakdown];

            // [WORKAROUND] Silently change state (notify: false) to avoid component reinitialization
            // and notify directly with $zemStateChangeStart and $zemStateChangeSuccess
            $rootScope.$broadcast('$zemStateChangeStart');
            $state.go('v2.analytics', {
                id: id,
                level: levelStateParam,
                breakdown: breakdownStateParam
            }, {notify: false, location: 'replace'}).then(function () {
                $rootScope.$broadcast('$zemStateChangeSuccess');
            });
        }
    }
});

