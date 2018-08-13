angular.module('one.widgets').component('zemCampaignBudgetsSettings', {
    bindings: {
        entity: '<',
        errors: '<',
        api: '<',
    },
    template: require('./zemCampaignBudgetsSettings.component.html'),
    controller: function(
        $scope,
        $q,
        $uibModal,
        zemPermissions,
        zemCampaignBudgetsEndpoint,
        zemNavigationNewService
    ) {
        // eslint-disable-line max-len
        var $ctrl = this;
        $ctrl.options = options;
        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
        $ctrl.stateReloadNeeded = false;

        $ctrl.$onInit = function() {
            $ctrl.activeAccount = zemNavigationNewService.getActiveAccount();
            $ctrl.api.register({
                isStateReloadNeeded: function() {
                    return $ctrl.stateReloadNeeded;
                },
            });
            $ctrl.showCollapsed = false;
        };

        $ctrl.$onChanges = function() {
            if (!$ctrl.entity) return;

            load();
        };

        function load() {
            $ctrl.loadingInProgress = true;
            zemCampaignBudgetsEndpoint.list($ctrl.entity.id).then(
                function(data) {
                    $ctrl.loadingInProgress = false;
                    $ctrl.budgets = data;
                },
                function() {
                    $ctrl.loadingInProgress = false;
                }
            );
        }

        function refresh(updatedId) {
            $ctrl.updatedId = updatedId;
            load();
        }
        function openModal() {
            var modal = $uibModal.open({
                component: 'zemCampaignBudgetsModal',
                backdrop: 'static',
                keyboard: false,
                size: 'wide',
                resolve: {
                    selectedBudgetId: function() {
                        return $ctrl.selectedBudgetId;
                    },
                    campaign: function() {
                        return $ctrl.entity;
                    },
                    budgets: function() {
                        return $ctrl.budgets;
                    },
                },
            });

            modal.result.then(function(data) {
                if (data) {
                    refresh();
                    $ctrl.stateReloadNeeded = true;
                }
            });
        }

        $ctrl.getAvailableCredit = function(all, include) {
            if (!$ctrl.budgets) return [];
            return all
                ? $ctrl.budgets.credits
                : $ctrl.budgets.credits.filter(function(obj) {
                      return (
                          (include && obj.id === include) ||
                          (!include && obj.isAvailable)
                      );
                  });
        };

        $ctrl.addBudgetItem = function() {
            $ctrl.selectedBudgetId = null;
            return openModal();
        };
        $ctrl.editBudgetItem = function(id) {
            $ctrl.selectedBudgetId = id;
            return openModal();
        };

        $ctrl.canAccessPlatformCosts = function() {
            return zemPermissions.canAccessPlatformCosts($ctrl.activeAccount);
        };

        $ctrl.canAccessAgencyCosts = function() {
            return zemPermissions.canAccessAgencyCosts($ctrl.activeAccount);
        };
    },
});
