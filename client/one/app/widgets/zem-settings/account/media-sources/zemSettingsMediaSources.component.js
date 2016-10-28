angular.module('one.widgets').component('zemSettingsMediaSources', {
    bindings: {
        account: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/account/media-sources/zemSettingsMediaSources.component.html',
    controller: ['zemPermissions', function (zemPermissions) {
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

        function getAllowedMediaSources () {
            if (!$ctrl.account) return;
            var list = [];
            angular.forEach($ctrl.account.settings.allowedSources, function (value, key) {
                if (value.allowed) {
                    value.value = key;
                    this.push(value);
                }
            }, list);
            return list;
        }

        function getAvailableMediaSources () {
            if (!$ctrl.account) return;
            var list = [];
            angular.forEach($ctrl.account.settings.allowedSources, function (value, key) {
                if (!value.allowed) {
                    value.value = key;
                    this.push(value);
                }
            }, list);
            return list;
        }

        function addToAllowedMediaSources () {
            angular.forEach($ctrl.selectedMediaSources.available, function (value) {
                $ctrl.account.settings.allowedSources[value].allowed = true;
            });
            $ctrl.selectedMediaSources.allowed.length = 0;
            $ctrl.selectedMediaSources.available.length = 0;
        }

        function removeFromAllowedMediaSources () {
            angular.forEach($ctrl.selectedMediaSources.allowed, function (value) {
                $ctrl.account.settings.allowedSources[value].allowed = false;
            });
            $ctrl.selectedMediaSources.available.length = 0;
            $ctrl.selectedMediaSources.allowed.length = 0;
        }
    }],
});
