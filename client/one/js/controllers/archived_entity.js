/* globals $, angular, constants */
angular.module('one.legacy').controller('ArchivedEntityCtrl', function ($scope, zemNavigationService, zemNavigationNewService, zemEntityService) { // eslint-disable-line max-len
    // FIXME: This is temporary Controller for handling Entity archived state and
    // will be replaced when migrating to new routing and page layout.
    // Atm, this is simplest solution

    $scope.requestInProgress = false;
    $scope.restore = restore;
    $scope.getEntityTypeName = getEntityTypeName;
    init();

    function init () {
        $scope.entity = zemNavigationNewService.getActiveEntity();
        if (!$scope.entity) {
            // Can happen during app initialization (proper solution will be made on refactor)
            var destroyHandler = zemNavigationNewService.onActiveEntityChange(function () {
                destroyHandler();
                $scope.entity = zemNavigationNewService.getActiveEntity();
            });
        }
    }

    function restore () {
        $scope.requestInProgress = true;
        zemEntityService.executeAction(constants.entityAction.RESTORE, $scope.entity.type, $scope.entity.id)
        .then(updateNavigationCache).then(zemNavigationNewService.refreshState).finally (function () {
            $scope.requestInProgress = false;
        });
    }

    function updateNavigationCache () {
        // TODO - delete (this will not be needed after removing zemNavigationService)
        if ($scope.entity.type === constants.entityType.AD_GROUP) {
            return zemNavigationService.reloadAdGroup($scope.entity.id);
        }
        if ($scope.entity.type === constants.entityType.CAMPAIGN) {
            return zemNavigationService.reloadCampaign($scope.entity.id);
        }
        if ($scope.entity.type === constants.entityType.ACCOUNT) {
            return zemNavigationService.reloadAccount($scope.entity.id);
        }
    }

    function getEntityTypeName () {
        if (!$scope.entity) return;
        if ($scope.entity.type === constants.entityType.ACCOUNT) return 'Account';
        if ($scope.entity.type === constants.entityType.CAMPAIGN) return 'Campaign';
        if ($scope.entity.type === constants.entityType.AD_GROUP) return 'Ad Group';
    }
});
