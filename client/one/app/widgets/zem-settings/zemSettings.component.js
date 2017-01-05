angular.module('one.widgets').component('zemSettings', {
    templateUrl: '/app/widgets/zem-settings/zemSettings.component.html',
    controller: function ($timeout, hotkeys, zemSettingsService, zemEntityService) {
        var $ctrl = this;
        $ctrl.currentContainer = null;
        $ctrl.currentContainerType = null;

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

        function register (type, entitySettingsComponent) {
            $ctrl.currentContainer = entitySettingsComponent;
            $ctrl.currentContainerType = type;
        }

        function open () {
            $ctrl.entity = zemSettingsService.getCurrentEntity();
            $timeout(function () {
                $ctrl.sidePanel.open();
            }, 0);

            zemEntityService.getEntity($ctrl.entity.type, $ctrl.entity.id).then(function (entity) {
                entity.id = $ctrl.entity.id;
                entity.type = $ctrl.entity.type;
                $ctrl.currentContainer.load(entity);
            });
        }

        function close () {
            if ($ctrl.currentContainer.isDirty()) {
                var close = confirm('You have unsaved changes. \nAre you sure you want to close settings?'); // eslint-disable-line
                if (!close) return;
            }

            $ctrl.sidePanel.close();
            $timeout(function () {
                if (!$ctrl.sidePanel.isVisible()) {
                    $ctrl.entity = null;
                }
            }, 500);
        }
    }
});
