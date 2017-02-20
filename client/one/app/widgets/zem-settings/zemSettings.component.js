angular.module('one.widgets').component('zemSettings', {
    templateUrl: '/app/widgets/zem-settings/zemSettings.component.html',
    controller: function ($timeout, $state, hotkeys, zemSettingsService, zemEntityService) {
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

        function open (event, payload) {
            var entity = null;
            var visible = false;
            $ctrl.entity = payload.entity;

            // Make side-panel animation smooth
            // At first wait for initial render (empty settings)
            // after that trigger open and wait for animation to end (400ms should be enough)
            // and then load entity (this depends fetch status - finished before or after side panel is opened)
            $timeout(function () {
                $ctrl.sidePanel.open();
                $timeout(function () {
                    visible = true;
                    if (entity) {
                        $ctrl.currentContainer.load(entity);
                        if (payload.scrollToComponent) $ctrl.currentContainer.scrollTo(payload.scrollToComponent);
                    }
                }, 400);
            }, 0);

            zemEntityService.getEntity($ctrl.entity.type, $ctrl.entity.id).then(function (e) {
                e.id = $ctrl.entity.id;
                e.type = $ctrl.entity.type;
                if (visible) {
                    $ctrl.currentContainer.load(e);
                    if (payload.scrollToComponent) $ctrl.currentContainer.scrollTo(payload.scrollToComponent);
                } else {
                    entity = e;
                }
            });
        }

        function close () {
            if ($ctrl.currentContainer.isDirty()) {
                var close = confirm('You have unsaved changes. \nAre you sure you want to close settings?'); // eslint-disable-line
                if (!close) return;
            }

            var stateReloadNeeded = $ctrl.currentContainer.isStateReloadNeeded();

            $ctrl.sidePanel.close();
            $timeout(function () {
                if (!$ctrl.sidePanel.isVisible()) {
                    $ctrl.entity = null;
                }

                if (stateReloadNeeded) $state.reload();
            }, 500);
        }
    }
});
