var commonHelpers = require('../../../../../shared/helpers/common.helpers');
var ScopeSelectorState = require('../../../../../shared/components/scope-selector/scope-selector.constants')
    .ScopeSelectorState;

angular.module('one.widgets').component('zemPublisherGroupsUpload', {
    template: require('./zemPublisherGroupsUpload.component.html'),
    bindings: {
        resolve: '<',
        modalInstance: '<',
    },
    controller: function(
        $scope,
        zemPublisherGroupsEndpoint,
        zemPermissions,
        zemAccountService
    ) {
        var $ctrl = this;

        $ctrl.isCreationMode = false;

        $ctrl.upsert = upsert;
        $ctrl.clearValidationError = clearValidationError;
        $ctrl.fileUploadCallback = fileUploadCallback;
        $ctrl.downloadErrors = downloadErrors;
        $ctrl.downloadExample = downloadExample;
        $ctrl.onScopeStateChange = onScopeStateChange;
        $ctrl.onAccountChange = onAccountChange;

        $ctrl.errors = null;
        $ctrl.putRequestInProgress = false;
        $ctrl.isAgencyScopeDisabled = false;
        $ctrl.isAccountScopeDisabled = false;
        $ctrl.accounts = [];
        $ctrl.agencyId = null;
        $ctrl.accountId = null;

        $ctrl.$onInit = function() {
            if ($ctrl.resolve) {
                if ($ctrl.resolve.agency) {
                    $ctrl.agencyId = $ctrl.resolve.agency.id;
                }
                if ($ctrl.resolve.account) {
                    $ctrl.accountId = $ctrl.resolve.account.id;
                }
            }

            $ctrl.hasAgencyScope = false;
            if (commonHelpers.isDefined($ctrl.agencyId)) {
                $ctrl.hasAgencyScope = zemPermissions.hasAgencyScope(
                    $ctrl.agencyId
                );
                getAccountsForAgency($ctrl.agencyId, function(accounts) {
                    $ctrl.accounts = accounts;
                });
            }

            $ctrl.formData = initFormData();
        };

        function initFormData() {
            var formData = {};
            if (
                $ctrl.resolve.publisherGroup &&
                $ctrl.resolve.publisherGroup.id
            ) {
                formData = {
                    id: $ctrl.resolve.publisherGroup.id,
                    name: $ctrl.resolve.publisherGroup.name,
                    include_subdomains:
                        $ctrl.resolve.publisherGroup.include_subdomains,
                    scopeState: getScopeState(
                        $ctrl.resolve.publisherGroup.id,
                        $ctrl.resolve.publisherGroup.agency_id
                    ),
                    agencyId:
                        $ctrl.resolve.publisherGroup.agency_id ||
                        $ctrl.agencyId,
                    accountId:
                        $ctrl.resolve.publisherGroup.account_id ||
                        $ctrl.accountId,
                };
            } else {
                $ctrl.isCreationMode = true;
                formData.include_subdomains = true;
                formData.scopeState = getScopeState(null, null);
                formData.agencyId = $ctrl.agencyId ? $ctrl.agencyId + '' : null;
                formData.accountId = $ctrl.accountId
                    ? $ctrl.accountId + ''
                    : null;
            }

            return formData;
        }

        function upsert() {
            $ctrl.putRequestInProgress = true;
            zemPublisherGroupsEndpoint
                .upsert($ctrl.formData)
                .then(function() {
                    $ctrl.modalInstance.close();
                })
                .catch(function(data) {
                    $ctrl.errors = data;
                })
                .finally(function() {
                    $ctrl.putRequestInProgress = false;
                });
        }

        function clearValidationError(field) {
            if (!$ctrl.errors) {
                return;
            }

            if ($ctrl.errors.hasOwnProperty(field)) {
                delete $ctrl.errors[field];
            }

            if (
                field === 'entries' &&
                $ctrl.errors.hasOwnProperty('errors_csv_key')
            ) {
                delete $ctrl.errors.errors_csv_key;
            }
        }

        function fileUploadCallback(file) {
            $ctrl.formData.file = file;
            $scope.$digest();
        }

        function downloadErrors() {
            zemPublisherGroupsEndpoint.downloadErrors(
                $ctrl.resolve.account.id,
                $ctrl.resolve.agency.id,
                $ctrl.errors.errors_csv_key
            );
        }

        function downloadExample() {
            zemPublisherGroupsEndpoint.downloadExample();
        }

        function onScopeStateChange($event) {
            $ctrl.formData.scopeState = $event;
        }

        function onAccountChange($event) {
            $ctrl.formData.account = $event;
        }

        function getAccountsForAgency(agencyId, callback) {
            zemAccountService.list(agencyId, function() {}).subscribe(callback);
        }

        function getScopeState(publisherGroupId, agencyId) {
            var scopeState;

            if (!commonHelpers.isDefined(publisherGroupId)) {
                if ($ctrl.accountId === null && $ctrl.hasAgencyScope === true) {
                    scopeState = ScopeSelectorState.AGENCY_SCOPE;
                } else {
                    scopeState = ScopeSelectorState.ACCOUNT_SCOPE;
                }
            } else if (commonHelpers.isDefined(agencyId)) {
                scopeState = ScopeSelectorState.AGENCY_SCOPE;
            } else {
                scopeState = ScopeSelectorState.ACCOUNT_SCOPE;
            }

            return scopeState;
        }
    },
});
