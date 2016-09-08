/* globals oneApp, constants */
'use strict';

angular.module('one.widgets').component('zemHeaderNavigation', { // eslint-disable-line max-len
    templateUrl: '/app/widgets/zem-header/components/zem-header-navigation/zemHeaderNavigation.component.html',
    controller: ['$scope', '$element', 'hotkeys', function ($scope, $element, hotkeys) {
        var $ctrl = this;

        $ctrl.open = false;
        $ctrl.onToggle = onToggle;

        $ctrl.$onInit = function () {
            initializeShortcuts();
        };

        function initializeShortcuts () {
            hotkeys.bindTo($scope).add({combo: 'f', callback: open});
            hotkeys.bindTo($scope).add({combo: 'enter', allowIn: ['INPUT'], callback: close});
        }

        function open () {
            $ctrl.open = true;
        }

        function close () {
            $ctrl.open = false;
        }

        function onToggle (open) {
            if (open) {
                // Focus input on open
                $element.find('zem-navigation input').focus();
            } else {
                // Reset zem-navigation filter input
                $element.find('zem-navigation input').val('');
                $element.find('zem-navigation input').triggerHandler('change');
            }
        }
    }]
});
