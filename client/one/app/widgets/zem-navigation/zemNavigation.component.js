/* globals oneApp, constants */
'use strict';

angular.module('one.widgets').component('zemNavigation', { // eslint-disable-line max-len
    templateUrl: '/app/widgets/zem-navigation/zemNavigation.component.html',
    controller: ['$scope', '$state', '$element', 'zemNavigationUtils', 'zemNavigationService', 'zemFilterService', function ($scope, $state, $element, zemNavigationUtils, zemNavigationService, zemFilterService) {
        // TODO: prepare navigation service
        // TODO: check active entity -> bold - $state.includes('main.campaigns', { id: campaign.id.toString()})

        var $ctrl = this;
        $ctrl.query = '';
        $ctrl.list = [];

        $ctrl.filter = filterList;
        $ctrl.navigateTo = navigateTo;
        $ctrl.getItemClasses = getItemClasses;
        $ctrl.getItemIconClass = getItemIconClass;

        initialize();

        function initialize () {
            // TODO: Update zemNavigationService
            zemNavigationService.onUpdate($scope, initializeList);
        }

        function getItemClasses (item) {
            var classes = [];
            if (item.data.archived) classes.push('archived');
            if (item.active) classes.push('active');
            if (item.type === constants.entityType.ACCOUNT) classes.push('account');
            if (item.type === constants.entityType.CAMPAIGN) classes.push('campaign');
            if (item.type === constants.entityType.AD_GROUP) classes.push('ad-group');
            return classes;
        }

        function getItemIconClass (item) {
            if (item.type !== constants.entityType.AD_GROUP) return 'none';

            var adGroup = item.data;
            if (adGroup.reloading) return 'reloading';
            if (adGroup.active === constants.infoboxStatus.STOPPED) return 'stopped';
            if (adGroup.active === constants.infoboxStatus.LANDING_MODE) return 'landing';
            if (adGroup.active === constants.infoboxStatus.INACTIVE) return 'inactive';
            if (adGroup.active === constants.infoboxStatus.AUTOPILOT) return 'autopilot';
            return 'active';
        }

        function initializeList () {
            $ctrl.list = zemNavigationUtils.convertToEntityList(zemNavigationService.getAccounts());
            filterList($ctrl.query);
        }

        function filterList (query) {
            var showArchived = zemFilterService.getShowArchived();
            $ctrl.filteredList = zemNavigationUtils.filterEntityList($ctrl.list, query, showArchived);
            scrollToTop();
        }

        function scrollToTop () {
            $element.find('.scroll-container').scrollTop(0);
        }

        //
        // TODO Refactor: move to new navigation service
        //
        function navigateTo (item) {
            var state = '';
            switch (item.type) {
            case constants.entityType.ACCOUNT:
                state = 'main.accounts';
                break;
            case constants.entityType.CAMPAIGN:
                state = 'main.campaigns';
                break;
            case constants.entityType.AD_GROUP:
                state = 'main.adGroups';
                break;
            }
            // keep the same tab if possible
            if ($state.includes('**.sources')) {
                state += '.sources';
            }
            if ($state.includes('**.history')) {
                state += '.history';
            }
            if ($state.includes('**.settings')) {
                state += '.settings';
            }

            // TODO: check permissions - account - campaign, history, sources view
            $state.go(state, {id: item.data.id});
        }
    }]
});
