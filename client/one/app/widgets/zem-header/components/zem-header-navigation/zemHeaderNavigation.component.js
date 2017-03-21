angular.module('one.widgets').component('zemHeaderNavigation', {
    templateUrl: '/app/widgets/zem-header/components/zem-header-navigation/zemHeaderNavigation.component.html',
    controller: function ($scope, $element, $timeout, config, hotkeys, zemHeaderNavigationService) { // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.config = config;
        $ctrl.open = false;
        $ctrl.onToggle = onToggle;

        $ctrl.$onInit = function () {
            initializeShortcuts();
        };

        function initializeShortcuts () {
            hotkeys.bindTo($scope).add({combo: 'f', callback: open});
            hotkeys.bindTo($scope).add({combo: 'enter', allowIn: ['INPUT'], callback: close});

            hotkeys.bindTo($scope).add({combo: 'ctrl+up', callback: zemHeaderNavigationService.quickNavigate});
            hotkeys.bindTo($scope).add({combo: 'ctrl+down', callback: zemHeaderNavigationService.quickNavigate});
            hotkeys.bindTo($scope).add({combo: 'ctrl+left', callback: zemHeaderNavigationService.quickNavigate});
            hotkeys.bindTo($scope).add({combo: 'ctrl+right', callback: zemHeaderNavigationService.quickNavigate});
        }

        function open () {
            $ctrl.open = true;
        }

        function close () {
            $ctrl.open = false;
        }

        function onToggle (open) {
            if (open) {
                // Focus input on open (wait for animation to finish)
                $timeout(function () {
                    $element.find('zem-navigation input').focus();
                }, 250);
            } else {
                // Reset zem-navigation filter input
                $element.find('zem-navigation input').val('');
                $element.find('zem-navigation input').triggerHandler('change');
            }
        }
    }
});
