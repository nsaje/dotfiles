// TODO: Fix Performance issues with ui-select - accountManagers (500+)

angular.module('one.widgets').component('zemAccountGeneralSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    template: require('./zemAccountGeneralSettings.component.html'),
    controller: function (zemPermissions) {
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;

        $ctrl.updateAgencyDefaults = updateAgencyDefaults;
        $ctrl.agencySelect2Config = {
            // TODO: Refactor
            dropdownCssClass: 'service-fee-select2',
            createSearchChoice: function (term, data) {
                if ($(data).filter(function () { return this.text.localeCompare(term) === 0; }).length === 0) {
                    return {id: term, text: term + ' (Create new agency)'};
                }
            },
            data: function () {
                return {
                    results: $ctrl.entity ? $ctrl.entity.agencies.map(convertSelect2) : [],
                };
            },
        };

        $ctrl.$onInit = function () {
            $ctrl.api.register({
                // Not needed (placeholder)
            });
        };

        function updateAgencyDefaults () {
            if ($ctrl.entity.settings.agency && $ctrl.entity.settings.agency.obj) {
                if ($ctrl.entity.settings.accountType === constants.accountTypes.UNKNOWN) {
                    $ctrl.entity.settings.accountType = $ctrl.entity.settings.agency.obj.defaultAccountType;
                }
                if (!$ctrl.entity.settings.defaultSalesRepresentative) {
                    $ctrl.entity.settings.defaultSalesRepresentative =
                        $ctrl.entity.settings.agency.obj.salesRepresentative.toString();
                }
                if (!$ctrl.entity.settings.defaultCsRepresentative) {
                    $ctrl.entity.settings.defaultCsRepresentative =
                        $ctrl.entity.settings.agency.obj.csRepresentative.toString();
                }
                if (!$ctrl.entity.settings.obRepresentative) {
                    $ctrl.entity.settings.obRepresentative =
                        $ctrl.entity.settings.agency.obj.obRepresentative.toString();
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
    },
});
