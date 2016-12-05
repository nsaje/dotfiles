angular.module('one.widgets').component('zemSettings', {
    templateUrl: '/app/widgets/zem-settings/zemSettings.component.html',
    controller: function ($timeout, hotkeys, zemSettingsService) {
        var $ctrl = this;
        $ctrl.constants = constants;
        $ctrl.sidePanel = {};
        $ctrl.onCloseRequest = zemSettingsService.close;
        $ctrl.api = {
            register: register,
            close: zemSettingsService.close
        };

        $ctrl.$onInit = function () {
            hotkeys.add({combo: 's', callback: function () { zemSettingsService.open(); }});

            $ctrl.onRequestClose = zemSettingsService.close;
            zemSettingsService.onOpen(open);
            zemSettingsService.onClose(close);
        };

        function register (entitySettingsComponent) {
            $ctrl.entitySettingsComponent = entitySettingsComponent;
            $ctrl.entitySettingsComponent.load();
        }

        function open () {
            $ctrl.entity = zemSettingsService.getCurrentEntity();
            $ctrl.sidePanel.open();
        }

        function close () {
            if ($ctrl.entitySettingsComponent.isDirty()) {
                var close = confirm('You have unsaved changes. \nAre you sure you want to close settings?');
                if (!close) return;
            }

            $ctrl.sidePanel.close();
            $timeout(function () {
                if (!$ctrl.sidePanel.isVisible()) {
                    $ctrl.entity = null;
                    $ctrl.entitySettingsComponent = null;
                }
            }, 500);
        }
    }
});
