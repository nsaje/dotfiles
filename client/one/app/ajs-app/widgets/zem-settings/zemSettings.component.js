require('./zemSettings.component.less');

angular.module('one.widgets').component('zemSettings', {
    template: require('./zemSettings.component.html'),
    controller: function(
        $timeout,
        $state,
        hotkeys,
        zemSettingsService,
        zemEntityService
    ) {
        var $ctrl = this;
        $ctrl.currentContainer = null;
        $ctrl.currentContainerType = null;

        $ctrl.constants = constants;
        $ctrl.sidePanel = {};
        $ctrl.onCloseRequest = zemSettingsService.close;
        $ctrl.api = {
            register: register,
            close: zemSettingsService.close,
        };

        var openSettingsHandler, closeSettingsHandler;

        $ctrl.$onInit = function() {
            zemSettingsService.init();

            hotkeys.add({
                combo: 's',
                callback: function() {
                    zemSettingsService.open();
                },
            });

            $ctrl.onRequestClose = zemSettingsService.close;
            openSettingsHandler = zemSettingsService.onOpen(open);
            closeSettingsHandler = zemSettingsService.onClose(close);
        };

        $ctrl.$onDestroy = function() {
            if (openSettingsHandler) openSettingsHandler();
            if (closeSettingsHandler) closeSettingsHandler();
            hotkeys.del('s');
        };

        function register(type, entitySettingsComponent) {
            $ctrl.currentContainer = entitySettingsComponent;
            $ctrl.currentContainerType = type;
        }

        function open(event, payload) {
            var entity = null;
            var visible = false;
            $ctrl.entity = payload.entity;

            // Make side-panel animation smooth
            // At first wait for initial render (empty settings)
            // after that trigger open and wait for animation to end (400ms should be enough)
            // and then load entity (this depends fetch status - finished before or after side panel is opened)
            $timeout(function() {
                $ctrl.sidePanel.open();
                $timeout(function() {
                    visible = true;
                    if (entity) {
                        $ctrl.currentContainer.load(entity);
                        if (payload.scrollToComponent)
                            $ctrl.currentContainer.scrollTo(
                                payload.scrollToComponent
                            );
                    }
                }, 400);
            }, 0);

            zemEntityService
                .getEntity($ctrl.entity.type, $ctrl.entity.id)
                .then(function(e) {
                    // FIXME: find better solution to merge entity settings
                    e.id = $ctrl.entity.id;
                    e.type = $ctrl.entity.type;
                    copyParents(e, $ctrl.entity);

                    if (visible) {
                        $ctrl.currentContainer.load(e);
                        if (payload.scrollToComponent)
                            $ctrl.currentContainer.scrollTo(
                                payload.scrollToComponent
                            );
                    } else {
                        entity = e;
                    }
                });
        }

        function copyParents(eDest, eSource) {
            if (eSource.parent) {
                eDest.parent = {
                    id: eSource.parent.id,
                    type: eSource.parent.type,
                };

                copyParents(eDest.parent, eSource.parent);
            }
        }

        function close() {
            if ($ctrl.currentContainer.isDirty()) {
                // prettier-ignore
                var close = confirm('You have unsaved changes. \nAre you sure you want to close settings?'); // eslint-disable-line
                if (!close) return;
            }

            var stateReloadNeeded = $ctrl.currentContainer.isStateReloadNeeded();

            $ctrl.sidePanel.close();
            $timeout(function() {
                if (!$ctrl.sidePanel.isVisible()) {
                    $ctrl.entity = null;
                }

                if (stateReloadNeeded) $state.reload();
            }, 500);
        }
    },
});
