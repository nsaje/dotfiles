angular.module('one.widgets').component('zemMediaSourcesSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/account/media-sources/zemMediaSourcesSettings.component.html',
    controller: function (zemPermissions) {
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.selectedMediaSources = {
            allowed: [],
            available: [],
        };

        $ctrl.getAllowedMediaSources = getAllowedMediaSources;
        $ctrl.getAvailableMediaSources = getAvailableMediaSources;
        $ctrl.addToAllowedMediaSources = addToAllowedMediaSources;
        $ctrl.removeFromAllowedMediaSources = removeFromAllowedMediaSources;

        $ctrl.$onInit = function () {
            $ctrl.api.register({
                // Not needed (placeholder)
            });
        };

        function getAllowedMediaSources () {
            if (!$ctrl.entity) return;
            var list = [];
            angular.forEach($ctrl.entity.settings.allowedSources, function (value, key) {
                if (value.allowed) {
                    value.value = key;
                    this.push(value);
                }
            }, list);
            return list;
        }

        function getAvailableMediaSources () {
            if (!$ctrl.entity) return;
            var list = [];
            angular.forEach($ctrl.entity.settings.allowedSources, function (value, key) {
                if (!value.allowed) {
                    value.value = key;
                    this.push(value);
                }
            }, list);
            return list;
        }

        function addToAllowedMediaSources () {
            angular.forEach($ctrl.selectedMediaSources.available, function (value) {
                $ctrl.entity.settings.allowedSources[value].allowed = true;
            });
            $ctrl.selectedMediaSources.allowed.length = 0;
            $ctrl.selectedMediaSources.available.length = 0;
        }

        function removeFromAllowedMediaSources () {
            angular.forEach($ctrl.selectedMediaSources.allowed, function (value) {
                $ctrl.entity.settings.allowedSources[value].allowed = false;
            });
            $ctrl.selectedMediaSources.available.length = 0;
            $ctrl.selectedMediaSources.allowed.length = 0;
        }
    },
});
