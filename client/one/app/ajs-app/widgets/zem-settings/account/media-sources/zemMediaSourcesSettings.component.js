angular.module('one.widgets').component('zemMediaSourcesSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    template: require('./zemMediaSourcesSettings.component.html'),
    controller: function(zemPermissions) {
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.selectedMediaSources = {
            allowed: [],
            available: [],
        };

        $ctrl.mediaSources = {
            allowed: [],
            available: [],
        };

        $ctrl.getAllowedMediaSources = getAllowedMediaSources;
        $ctrl.getAvailableMediaSources = getAvailableMediaSources;
        $ctrl.addToAllowedMediaSources = addToAllowedMediaSources;
        $ctrl.removeFromAllowedMediaSources = removeFromAllowedMediaSources;
        $ctrl.getSourceText = getSourceText;

        $ctrl.$onInit = function() {
            $ctrl.api.register({
                // Not needed (placeholder)
            });
        };

        $ctrl.$onChanges = function() {
            initialize();
        };

        function initialize() {
            $ctrl.selectedMediaSources.available = [];
            $ctrl.selectedMediaSources.allowed = [];
            $ctrl.mediaSources.allowed = getAllowedMediaSources();
            $ctrl.mediaSources.available = getAvailableMediaSources();
        }

        function getAllowedMediaSources() {
            if (!$ctrl.entity) return;

            var list = [];
            angular.forEach(
                $ctrl.entity.settings.allowedSources,
                function(value, key) {
                    if (value.allowed) {
                        this.push({
                            value: key,
                            released: value.released,
                            deprecated: value.deprecated,
                            name: value.name,
                        });
                    }
                },
                list
            );
            return list;
        }

        function getAvailableMediaSources() {
            if (!$ctrl.entity) return;

            var list = [];
            angular.forEach(
                $ctrl.entity.settings.allowedSources,
                function(value, key) {
                    if (!value.allowed) {
                        this.push({
                            value: key,
                            name: value.name,
                            released: value.released,
                            deprecated: value.deprecated,
                        });
                    }
                },
                list
            );
            return list;
        }

        function addToAllowedMediaSources() {
            angular.forEach($ctrl.selectedMediaSources.available, function(
                value
            ) {
                $ctrl.entity.settings.allowedSources[value].allowed = true;
            });

            initialize();
        }

        function removeFromAllowedMediaSources() {
            angular.forEach($ctrl.selectedMediaSources.allowed, function(
                value
            ) {
                $ctrl.entity.settings.allowedSources[value].allowed = false;
            });

            initialize();
        }

        function getSourceText(mediaSource) {
            var text = mediaSource.name;
            if (!mediaSource.released && mediaSource.deprecated) {
                text += ' (unreleased, deprecated)';
            } else if (!mediaSource.released) {
                text += ' (unreleased)';
            } else if (mediaSource.deprecated) {
                text += ' (deprecated)';
            }

            return text;
        }
    },
});
