angular.module('one.widgets').component('zemSettings', {
    templateUrl: '/app/widgets/zem-settings/zemSettings.component.html',
    controller: function ($timeout, hotkeys, zemSettingsService) {
        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.sidePanel = {};

        $ctrl.$onInit = function () {
            hotkeys.add({combo: 's', callback: function () { zemSettingsService.open(); }});

            zemSettingsService.onOpen(open);
            zemSettingsService.onClose(close);
        };

        function open () {
            $ctrl.entity = zemSettingsService.getCurrentEntity();
            $ctrl.sidePanel.open();
        }

        function close () {
            $ctrl.sidePanel.close();
            $timeout(function () {
                if (!$ctrl.sidePanel.isVisible()) {
                    $ctrl.entity = null;
                }
            }, 500);
        }
    }
});
