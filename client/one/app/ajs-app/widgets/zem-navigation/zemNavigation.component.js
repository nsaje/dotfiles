require('./zemNavigation.component.less');

angular.module('one.widgets').component('zemNavigation', {
    bindings: {
        isOpen: '<',
    },
    template: require('./zemNavigation.component.html'),
    controller: function(
        $scope,
        $element,
        $timeout,
        zemNavigationUtils,
        zemNavigationNewService,
        zemDataFilterService,
        NgZone
    ) {
        // eslint-disable-line max-len
        var KEY_UP_ARROW = 38;
        var KEY_DOWN_ARROW = 40;
        var KEY_ENTER = 13;

        var ITEM_HEIGHT_DEFAULT = 24; // NOTE: Change in CSS too!
        var ITEM_HEIGHT_ACCOUNT = 28; // NOTE: Change in CSS too!
        var ITEM_HEIGHT_CAMPAIGN = 24; // NOTE: Change in CSS too!
        var ITEM_HEIGHT_AD_GROUP = 24; // NOTE: Change in CSS too!

        var hierarchyUpdateHandler;

        var $ctrl = this;
        $ctrl.selectedEntity = null;
        $ctrl.activeEntity = null;
        $ctrl.query = '';
        $ctrl.list = null;
        $ctrl.filterInProgress = false;

        $ctrl.filter = filterList;
        $ctrl.navigateTo = navigateTo;
        $ctrl.getItemHref = getItemHref;
        $ctrl.getItemHeight = getItemHeight;
        $ctrl.getItemClasses = getItemClasses;
        $ctrl.getItemIconClass = getItemIconClass;

        $ctrl.$onInit = function() {
            hierarchyUpdateHandler = zemNavigationNewService.onHierarchyUpdate(
                initializeList
            );
            $element.keydown(handleKeyDown);
            initializeList();
        };

        $ctrl.$onChanges = function(changes) {
            if (changes.isOpen && $ctrl.isOpen) {
                filterList();
            }
        };

        $ctrl.$onDestroy = function() {
            if (hierarchyUpdateHandler) hierarchyUpdateHandler();
            $element.unbind();
        };

        function handleKeyDown(event) {
            if (!$ctrl.list) return;
            if (event.keyCode === KEY_UP_ARROW) upSelection(event);
            if (event.keyCode === KEY_DOWN_ARROW) downSelection(event);
            if (event.keyCode === KEY_ENTER) enterSelection(event);
            $scope.$digest();
        }

        function upSelection(event) {
            event.preventDefault();
            var idx = $ctrl.filteredList.indexOf($ctrl.selectedEntity);
            $ctrl.selectedEntity = $ctrl.filteredList[idx - 1];
            if (!$ctrl.selectedEntity) {
                $ctrl.selectedEntity =
                    $ctrl.filteredList[$ctrl.filteredList.length - 1];
            }
            scrollToItem($ctrl.selectedEntity);
        }

        function downSelection(event) {
            event.preventDefault();
            var idx = $ctrl.filteredList.indexOf($ctrl.selectedEntity);
            $ctrl.selectedEntity = $ctrl.filteredList[idx + 1];
            if (!$ctrl.selectedEntity) {
                $ctrl.selectedEntity = $ctrl.filteredList[0];
            }
            scrollToItem($ctrl.selectedEntity);
        }

        function enterSelection() {
            var entity = $ctrl.selectedEntity;
            if (!entity && $ctrl.query.length > 0) {
                // If searching select first item if no selection has been made
                entity = $ctrl.filteredList[0];
            }
            navigateTo(entity);
        }

        function getItemHeight(item) {
            // Return item's height defined in CSS because vs-repeat only works with predefined element heights
            if (item.type === constants.entityType.ACCOUNT)
                return ITEM_HEIGHT_ACCOUNT;
            if (item.type === constants.entityType.CAMPAIGN)
                return ITEM_HEIGHT_CAMPAIGN;
            if (item.type === constants.entityType.AD_GROUP)
                return ITEM_HEIGHT_AD_GROUP;
            return ITEM_HEIGHT_DEFAULT;
        }

        function getItemClasses(item) {
            var classes = [];
            if (item.data.archived)
                classes.push('zem-navigation__item--archived');
            if (item === $ctrl.activeEntity)
                classes.push('zem-navigation__item--active');
            if (item === $ctrl.selectedEntity)
                classes.push('zem-navigation__item--selected');
            if (item.type === constants.entityType.ACCOUNT)
                classes.push('zem-navigation__item--account');
            if (item.type === constants.entityType.CAMPAIGN)
                classes.push('zem-navigation__item--campaign');
            if (item.type === constants.entityType.AD_GROUP)
                classes.push('zem-navigation__item--group');
            return classes;
        }

        function getItemIconClass(item) {
            if (item.type !== constants.entityType.AD_GROUP)
                return 'zem-navigation__item-icon--none';

            var adGroup = item.data;
            if (adGroup.reloading)
                return 'zem-navigation__item-icon--reloading';
            if (
                adGroup.active === constants.infoboxStatus.STOPPED ||
                adGroup.active === constants.infoboxStatus.CAMPAIGNSTOP_STOPPED
            )
                return 'zem-navigation__item-icon--stopped';
            if (adGroup.active === constants.infoboxStatus.INACTIVE)
                return 'zem-navigation__item-icon--inactive';
            if (
                adGroup.active === constants.infoboxStatus.AUTOPILOT ||
                adGroup.active ===
                    constants.infoboxStatus
                        .CAMPAIGNSTOP_PENDING_BUDGET_AUTOPILOT
            )
                return 'zem-navigation__item-icon--autopilot';
            if (
                adGroup.active ===
                constants.infoboxStatus.CAMPAIGNSTOP_LOW_BUDGET
            )
                return 'zem-navigation__item-icon--active';
            return 'zem-navigation__item-icon--active';
        }

        function initializeList() {
            var hierarchy = zemNavigationNewService.getNavigationHierarchy();
            if (hierarchy) {
                $ctrl.list = zemNavigationUtils.convertToEntityList(hierarchy);
                if ($ctrl.isOpen) {
                    filterList();
                }
            }
        }

        function filterList() {
            if (!$ctrl.list) return;

            $ctrl.filterInProgress = true;
            $timeout(function() {
                doFilter();

                $ctrl.activeEntity = zemNavigationNewService.getActiveEntity();
                $ctrl.selectedEntity = null;
                $ctrl.filterInProgress = false;

                // If search in progress always scroll to top,
                // otherwise scroll to active entity
                if ($ctrl.query) {
                    scrollToTop();
                } else {
                    scrollToItem($ctrl.activeEntity, true); // Remove flickering in some cases
                    $timeout(function() {
                        scrollToItem($ctrl.activeEntity, true);
                    }); // Wait for list to be rendered first
                }
            }, 250);
        }

        function doFilter() {
            var showArchived = zemDataFilterService.getShowArchived();
            var activeAccount = zemNavigationNewService.getActiveAccount();

            $ctrl.entityList = activeAccount
                ? zemNavigationUtils.convertToEntityList(activeAccount)
                : null;

            var list = [];
            if ($ctrl.entityList && $ctrl.query.length === 0) {
                list = $ctrl.entityList;
            } else {
                list = $ctrl.list;
            }

            $ctrl.filteredList = zemNavigationUtils.filterEntityList(
                list,
                $ctrl.query,
                activeAccount,
                showArchived,
                true
            );
        }

        function scrollToTop() {
            $element.find('.zem-navigation__results').scrollTop(0);
        }

        function scrollToItem(item, scrollToMiddleIfOutside) {
            if (!item) return;

            // Scroll to item in case that is currently not shown
            // If it is lower in list scroll down so that it is displayed at the bottom,
            // otherwise scroll up to show it at the top.
            var $scrollContainer = $element.find('.zem-navigation__results');
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
                $scrollContainer.scrollTop(
                    selectedPos -
                        height +
                        getItemHeight($ctrl.filteredList[idx])
                );
            }
        }

        function getItemHref(entity) {
            var includeQueryParams = true;
            return zemNavigationNewService.getEntityHref(
                entity,
                includeQueryParams
            );
        }

        function navigateTo(entity) {
            NgZone.run(function() {
                zemNavigationNewService.navigateTo(entity);
            });
        }
    },
});
