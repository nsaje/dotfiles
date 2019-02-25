require('./zemGridContainerTabs.component.less');
var arrayHelpers = require('../../../../../shared/helpers/array.helpers');

angular.module('one.widgets').component('zemGridContainerTabs', {
    template: require('./zemGridContainerTabs.component.html'),
    bindings: {
        tabs: '<',
        entity: '<',
    },
    controller: function($rootScope, $state, $location, $window, zemUtils) {
        var $ctrl = this;

        $ctrl.navigateTo = navigateTo;
        $ctrl.hasOptions = hasOptions;

        $ctrl.$onInit = function() {};

        function navigateTo(event, tab, option) {
            var id = $ctrl.entity ? $ctrl.entity.id : null;
            var level = $ctrl.entity
                ? constants.entityTypeToLevelMap[$ctrl.entity.type]
                : constants.level.ALL_ACCOUNTS;
            var levelStateParam = constants.levelToLevelStateParamMap[level];
            var breakdownStateParam =
                constants.breakdownToBreakdownStateParamMap[
                    option ? option.breakdown : tab.breakdown
                ];
            var params = {
                id: id,
                level: levelStateParam,
                breakdown: breakdownStateParam,
            };

            if (zemUtils.shouldOpenInNewTab(event)) {
                $window.open(getStateHrefWithQueryParams(params), '_blank');
            } else {
                // [WORKAROUND] Silently change state (notify: false) to avoid component reinitialization
                // and notify directly with $zemStateChangeStart and $zemStateChangeSuccess
                $rootScope.$broadcast('$zemStateChangeStart');
                $state
                    .go('v2.analytics', params, {
                        notify: false,
                        location: 'replace',
                    })
                    .then(function() {
                        $rootScope.$broadcast('$zemStateChangeSuccess');
                    });
            }
        }

        function getStateHrefWithQueryParams(params) {
            var href = $state.href('v2.analytics', params);
            var queryParamsIndex = $location.url().indexOf('?');
            if (queryParamsIndex !== -1) {
                href += $location.url().slice(queryParamsIndex);
            }
            return href;
        }

        function hasOptions(tab) {
            return !arrayHelpers.isEmpty(tab.options);
        }
    },
});
