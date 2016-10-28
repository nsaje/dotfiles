// TODO: Fix Performance issues with ui-select - accountManagers (500+)

angular.module('one.widgets').component('zemAccountSettingsGeneral', {
    bindings: {
        account: '<',
        errors: '<',
        api: '<',
    },
    templateUrl: '/app/widgets/zem-settings/account/general/zemAccountSettingsGeneral.component.html',
    controller: ['zemPermissions', function (zemPermissions) {
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.updateAgencyDefaults = updateAgencyDefaults;
        $ctrl.agencySelect2Config = {
            dropdownCssClass: 'service-fee-select2',
            createSearchChoice: function (term, data) {
                if ($(data).filter(function () { return this.text.localeCompare(term) === 0; }).length === 0) {
                    return {id: term, text: term + ' (Create new agency)'};
                }
            },
            data: function () {
                return {
                    results: $ctrl.account ? $ctrl.account.agencies.map(convertSelect2) : [],
                };
            },
        };

        function updateAgencyDefaults () {
            if ($ctrl.account.settings.agency && $ctrl.account.settings.agency.obj) {
                if ($ctrl.account.settings.accountType === constants.accountTypes.UNKNOWN) {
                    $ctrl.account.settings.accountType = $ctrl.account.settings.agency.obj.defaultAccountType;
                }
                if (!$ctrl.account.settings.defaultSalesRepresentative) {
                    $ctrl.account.settings.defaultSalesRepresentative =
                        $ctrl.account.settings.agency.obj.salesRepresentative.toString();
                }
            }
        }

        var convertSelect2 = function (obj) {
            return {
                id: obj.name,
                text: obj.name,
                obj: obj,
            };
        };
    }],
});
