/* globals oneApp, constants */
'use strict';

angular.module('one.widgets').component('zemNavigation', { // eslint-disable-line max-len
    templateUrl: '/app/widgets/zem-navigation/zemNavigation.component.html',
    controller: ['$scope', '$state', '$element', 'hotkeys', 'zemNavigationUtils', 'zemNavigationService', 'zemFilterService', function ($scope, $state, $element, hotkeys, zemNavigationUtils, zemNavigationService, zemFilterService) {
        // TODO: prepare navigation service
        // TODO: check permission for filtering by agency
        // TODO: check active entity -> bold - $state.includes('main.campaigns', { id: campaign.id.toString()})
        var KEY_UP_ARROW = 38;
        var KEY_DOWN_ARROW = 40;
        var KEY_ENTER = 13;

        var $ctrl = this;
        $ctrl.query = '';
        $ctrl.list = null;
        $ctrl.selection = null;

        $ctrl.filter = filterList;
        $ctrl.navigateTo = navigateTo;
        $ctrl.getItemClasses = getItemClasses;
        $ctrl.getItemIconClass = getItemIconClass;

        $ctrl.$onInit = function () {
            // TODO: Update zemNavigationService
            zemNavigationService.onUpdate($scope, initializeList);
            $element.keydown(handleKeyDown);
        };

        function handleKeyDown (event) {
            if (event.keyCode === KEY_UP_ARROW) upSelection(event);
            if (event.keyCode === KEY_DOWN_ARROW) downSelection(event);
            if (event.keyCode === KEY_ENTER) enterSelection(event);
            $scope.$digest();
        }

        function upSelection (event) {
            event.preventDefault();
            var idx = $ctrl.filteredList.indexOf($ctrl.selection);
            $ctrl.selection = $ctrl.filteredList[idx - 1];
            scrollToItem($ctrl.selection);
        }

        function downSelection () {
            event.preventDefault();
            var idx = $ctrl.filteredList.indexOf($ctrl.selection);
            $ctrl.selection = $ctrl.filteredList[idx + 1];
            scrollToItem($ctrl.selection);
        }

        function enterSelection () {
            navigateTo($ctrl.selection);
        }

        function getItemClasses (item) {
            var classes = [];
            if (item.data.archived) classes.push('archived');
            if (item.active) classes.push('active');
            if (item === $ctrl.selection) classes.push('selected');
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
            if (!$ctrl.list) return;
            var showArchived = zemFilterService.getShowArchived();
            $ctrl.filteredList = zemNavigationUtils.filterEntityList($ctrl.list, query, showArchived);
            $ctrl.selection = null;
            scrollToTop();
        }

        function scrollToTop () {
            $element.find('.scroll-container').scrollTop(0);
        }

        function scrollToItem (item) {
            // Scroll to item in case that is currently not shown
            // If it is lower in list scroll down so that it is displayed at the bottom,
            // otherwise scroll up to show it at the top.
            var $scrollContainer = $element.find('.scroll-container');
            var height = $scrollContainer.height();
            var itemHeight = $element.find('.item').height();

            var idx = $ctrl.filteredList.indexOf(item);
            var selectedPos = idx * itemHeight;

            var viewFrom = $scrollContainer.scrollTop();
            var viewTo = viewFrom + height;

            if (selectedPos < viewFrom) {
                $scrollContainer.scrollTop(selectedPos);
            }

            if (selectedPos >= viewTo) {
                $scrollContainer.scrollTop(selectedPos - height + itemHeight);
            }
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
