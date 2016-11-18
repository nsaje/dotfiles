angular.module('one.widgets').component('zemSettings', {
    templateUrl: '/app/widgets/zem-settings/zemSettings.component.html',
    controller: function ($timeout, hotkeys, zemSettingsService) {
        var $ctrl = this;
        $ctrl.constants = constants;

        $ctrl.sidePanel = {};

        $ctrl.$onInit = function () {
            // Wire Open/Close through service - Service -> Component -> SidePanel
            $ctrl.onClose = zemSettingsService.close;
            hotkeys.add({combo: 's', callback: function () { zemSettingsService.open(); }});

            zemSettingsService.onOpen(open);
            zemSettingsService.onClose(onClose);
        };

        function open () {
            $ctrl.entity = zemSettingsService.getCurrentEntity();
            $ctrl.sidePanel.open();
        }

        function onClose () {
            $timeout(function () {
                if (!$ctrl.sidePanel.isVisible()) {
                    $ctrl.entity = null;
                }
            }, 500);
        }
    }
});
