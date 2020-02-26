require('./zemGridContainerTabs.component.less');

var commonHelpers = require('../../../../../shared/helpers/common.helpers');
var arrayHelpers = require('../../../../../shared/helpers/array.helpers');
var RoutePathName = require('../../../../../app.constants').RoutePathName;

angular.module('one.widgets').component('zemGridContainerTabs', {
    template: require('./zemGridContainerTabs.component.html'),
    bindings: {
        tabs: '<',
        entity: '<',
    },
    controller: function(NgRouter, $location, $window, zemUtils) {
        var $ctrl = this;

        $ctrl.navigateToStateWithQueryParams = navigateToStateWithQueryParams;
        $ctrl.getStateHrefWithQueryParams = getStateHrefWithQueryParams;
        $ctrl.hasOptions = hasOptions;

        $ctrl.$onInit = function() {};

        function navigateToStateWithQueryParams($event, tab, option) {
            $event.preventDefault();
            if (zemUtils.shouldOpenInNewTab($event)) {
                $window.open(
                    getStateHrefWithQueryParams(tab, option),
                    '_blank'
                );
            } else {
                var href = getStateHrefWithQueryParams(tab, option);
                NgRouter.navigateByUrl(href);
            }
        }

        function getStateHrefWithQueryParams(tab, option) {
            var urlTree = getUrlTree(tab, option);
            var href = NgRouter.createUrlTree(urlTree).toString();
            var queryParamsIndex = $location.url().indexOf('?');
            if (queryParamsIndex !== -1) {
                href += $location.url().slice(queryParamsIndex);
            }
            return href;
        }

        function getUrlTree(tab, option) {
            var urlTree = [RoutePathName.APP_BASE, RoutePathName.ANALYTICS];

            var level = $ctrl.entity
                ? constants.entityTypeToLevelMap[$ctrl.entity.type]
                : constants.level.ALL_ACCOUNTS;
            var levelParam = constants.levelToLevelParamMap[level];
            if (commonHelpers.isDefined(levelParam)) {
                urlTree.push(levelParam);
                var id = $ctrl.entity ? $ctrl.entity.id : null;
                if (commonHelpers.isDefined(id)) {
                    urlTree.push(id);
                }
            }

            var breakdownParam =
                constants.breakdownToBreakdownParamMap[
                    option ? option.breakdown : tab.breakdown
                ];
            if (commonHelpers.isDefined(breakdownParam)) {
                urlTree.push(breakdownParam);
            }

            return urlTree;
        }

        function hasOptions(tab) {
            return !arrayHelpers.isEmpty(tab.options);
        }
    },
});
