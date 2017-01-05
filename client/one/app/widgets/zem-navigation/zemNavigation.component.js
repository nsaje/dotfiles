angular.module('one.widgets').component('zemNavigation', {
    templateUrl: '/app/widgets/zem-navigation/zemNavigation.component.html',
    controller: function ($scope, $element, $timeout, hotkeys, zemPermissions, zemNavigationUtils, zemNavigationNewService, zemDataFilterService) { // eslint-disable-line max-len
        var KEY_UP_ARROW = 38;
        var KEY_DOWN_ARROW = 40;
        var KEY_ENTER = 13;

        var ITEM_HEIGHT_DEFAULT = 24; // NOTE: Change in CSS too!
        var ITEM_HEIGHT_ACCOUNT = 28; // NOTE: Change in CSS too!
        var ITEM_HEIGHT_CAMPAIGN = 24; // NOTE: Change in CSS too!
        var ITEM_HEIGHT_AD_GROUP = 24; // NOTE: Change in CSS too!

        var filteredStatusesUpdateHandler;

        var $ctrl = this;
        $ctrl.selectedEntity = null;
        $ctrl.activeEntity = null;
        $ctrl.query = '';
        $ctrl.list = null;
        $ctrl.showAgency = zemPermissions.hasPermission('zemauth.can_filter_by_agency');

        $ctrl.filter = filterList;
        $ctrl.navigateTo = navigateTo;
        $ctrl.getItemHref = getItemHref;
        $ctrl.getItemHeight = getItemHeight;
        $ctrl.getItemClasses = getItemClasses;
        $ctrl.getItemIconClass = getItemIconClass;

        $ctrl.$onInit = function () {
            zemNavigationNewService.onHierarchyUpdate(initializeList);
            zemNavigationNewService.onActiveEntityChange(initializeList);
            filteredStatusesUpdateHandler = zemDataFilterService.onFilteredStatusesUpdate(filterList);
            $element.keydown(handleKeyDown);
        };

        $ctrl.$onDestroy = function () {
            if (filteredStatusesUpdateHandler) filteredStatusesUpdateHandler();
        };

        function handleKeyDown (event) {
            if (event.keyCode === KEY_UP_ARROW) upSelection(event);
            if (event.keyCode === KEY_DOWN_ARROW) downSelection(event);
            if (event.keyCode === KEY_ENTER) enterSelection(event);
            $scope.$digest();
        }

        function upSelection (event) {
            event.preventDefault();
            var idx = $ctrl.filteredList.indexOf($ctrl.selectedEntity);
            $ctrl.selectedEntity = $ctrl.filteredList[idx - 1];
            if (!$ctrl.selectedEntity) {
                $ctrl.selectedEntity = $ctrl.filteredList[$ctrl.filteredList.length - 1];
            }
            scrollToItem($ctrl.selectedEntity);
        }

        function downSelection () {
            event.preventDefault();
            var idx = $ctrl.filteredList.indexOf($ctrl.selectedEntity);
            $ctrl.selectedEntity = $ctrl.filteredList[idx + 1];
            if (!$ctrl.selectedEntity) {
                $ctrl.selectedEntity = $ctrl.filteredList[0];
            }
            scrollToItem($ctrl.selectedEntity);
        }

        function enterSelection () {
            var entity = $ctrl.selectedEntity;
            if (!entity && $ctrl.query.length > 0) {
                // If searching select first item if no selection has been made
                entity = $ctrl.filteredList[0];
            }
            navigateTo(entity);
        }

        function getItemHeight (item) {
            // Return item's height defined in CSS because vs-repeat only works with predefined element heights
            if (item.type === constants.entityType.ACCOUNT) return ITEM_HEIGHT_ACCOUNT;
            if (item.type === constants.entityType.CAMPAIGN) return ITEM_HEIGHT_CAMPAIGN;
            if (item.type === constants.entityType.AD_GROUP) return ITEM_HEIGHT_AD_GROUP;
            return ITEM_HEIGHT_DEFAULT;
        }

        function getItemClasses (item) {
            var classes = [];
            if (item.data.archived) classes.push('archived');
            if (item === $ctrl.activeEntity) classes.push('active');
            if (item === $ctrl.selectedEntity) classes.push('selected');
            if (item.type === constants.entityType.ACCOUNT) classes.push('account');
            if (item.type === constants.entityType.CAMPAIGN) classes.push('campaign');
            if (item.type === constants.entityType.AD_GROUP) classes.push('group');
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
            var hierarchy = zemNavigationNewService.getNavigationHierarchy();
            if (hierarchy) {
                var account = zemNavigationNewService.getActiveAccount();
                $ctrl.activeEntity = zemNavigationNewService.getActiveEntity();
                $ctrl.list = zemNavigationUtils.convertToEntityList(hierarchy);
                $ctrl.entityList = account ? zemNavigationUtils.convertToEntityList(account) : null;
                filterList();
            }
        }

        function filterList () {
            if (!$ctrl.list) return;
            var showArchived = zemDataFilterService.getShowArchived();

            var list = $ctrl.list;
            if ($ctrl.entityList && $ctrl.query.length === 0) {
                list = $ctrl.entityList;
            }

            $ctrl.filteredList = zemNavigationUtils.filterEntityList(list, $ctrl.query, showArchived, $ctrl.showAgency);

            $ctrl.selectedEntity = null;

            // If search in progress always scroll to top,
            // otherwise scroll to active entity
            if ($ctrl.query) {
                scrollToTop();
            } else {
                scrollToItem($ctrl.activeEntity, true); // Remove flickering in some cases
                $timeout(function () { scrollToItem($ctrl.activeEntity, true); }); // Wait for list to be rendered first
            }
        }

        function scrollToTop () {
            $element.find('.scroll-container').scrollTop(0);
        }

        function scrollToItem (item, scrollToMiddleIfOutside) {
            if (!item) return;

            // Scroll to item in case that is currently not shown
            // If it is lower in list scroll down so that it is displayed at the bottom,
            // otherwise scroll up to show it at the top.
            var $scrollContainer = $element.find('.scroll-container');
            var height = $scrollContainer.height();

            var selectedPos = 0;
            var idx = $ctrl.filteredList.indexOf(item);
            for (var i = 0; i < idx; i++) {
                selectedPos += getItemHeight($ctrl.filteredList[i]);
            }

            var viewFrom = $scrollContainer.scrollTop();
            var viewTo = viewFrom + height;

            if (scrollToMiddleIfOutside) {
                // Scroll item to middle if outside of initial view
                // [ux] last item in initial view are also scrolled to the middle
                if (selectedPos > height - ITEM_HEIGHT_DEFAULT) {
                    selectedPos -= height / 2;
                    $scrollContainer.scrollTop(selectedPos);
                } else {
                    $scrollContainer.scrollTop(0);
                }
            } else if (selectedPos < viewFrom) {
                $scrollContainer.scrollTop(selectedPos);
            } else if (selectedPos >= viewTo) {
                $scrollContainer.scrollTop(selectedPos - height + getItemHeight($ctrl.filteredList[idx]));
            }
        }

        function getItemHref (entity) {
            return zemNavigationNewService.getEntityHref(entity, true);
        }

        function navigateTo (entity) {
            zemNavigationNewService.navigateTo(entity);
        }
    }
});
