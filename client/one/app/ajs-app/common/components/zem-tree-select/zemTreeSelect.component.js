require('./zemTreeSelect.component.less');

angular.module('one.common').component('zemTreeSelect', {
    bindings: {
        rootNode: '<',
        initialSelection: '<',
        onUpdate: '&',
    },
    template: require('./zemTreeSelect.component.html'),
    controller: function($scope, $element, $timeout, zemTreeSelectService) {
        //
        // Tree Node (input: $ctrl.rootNode)
        //  - name, id, value
        //  - navigationOnly (default - false)
        //  - childNodes: [nodes]
        //

        var $ctrl = this;
        $ctrl.ITEM_HEIGHT = 30;
        $ctrl.toggleItemState = toggleItemState;
        $ctrl.toggleCollapse = toggleCollapse;
        $ctrl.toggleSelection = toggleSelection;
        $ctrl.onSearch = onSearch;
        $ctrl.highlightItem = highlightItem;
        $ctrl.getParentsInfo = getParentsInfo;

        $ctrl.$onInit = function() {
            $ctrl.list = zemTreeSelectService.createList($ctrl.rootNode);
            $ctrl.filteredList = zemTreeSelectService.filterList($ctrl.list);
            highlightItem($ctrl.filteredList[0]);
            initializeSelection();
            initializeDropdownHandler();
        };

        function initializeSelection() {
            if (!$ctrl.initialSelection) return;

            var mapIds = {};
            $ctrl.list.forEach(function(node) {
                mapIds[node.id.toString()] = node;
            });
            $ctrl.initialSelection.forEach(function(id) {
                mapIds[id].selected = true;
            });

            $ctrl.selectedItems = $ctrl.list.filter(function(item) {
                return item.selected;
            });
        }

        function toggleDropdown() {
            if ($ctrl.dropdownVisible) {
                $ctrl.dropdownVisible = false;
                $ctrl.searchQuery = '';
            } else {
                $ctrl.dropdownVisible = true;
            }
        }

        function onSearch(searchQuery) {
            $ctrl.filteredList = zemTreeSelectService.filterList(
                $ctrl.list,
                searchQuery
            );
            highlightItem($ctrl.filteredList[0]);
        }

        function toggleCollapse(category) {
            category.isCollapsed = !category.isCollapsed;
            $ctrl.filteredList = zemTreeSelectService.filterList($ctrl.list);
        }

        function toggleItemState(item) {
            if (item.isLeaf || $ctrl.searchQuery) {
                toggleSelection(item);
            } else {
                toggleCollapse(item);
            }
        }

        function toggleSelection(item) {
            if (!item.isSelectable) return;
            item.selected = !item.selected;
            updateSelection();
        }

        function updateSelection() {
            $ctrl.selectedItems = $ctrl.list.filter(function(item) {
                return item.selected;
            });
            $ctrl.onUpdate({
                nodes: $ctrl.selectedItems.map(function(item) {
                    return item.value.id;
                }),
            });
        }

        function highlightItem(item) {
            $ctrl.highlightedItem = item;
        }

        function getParentsInfo(item) {
            if (!item.parentsInfo) {
                var p = item.parent;
                var parentNames = [];
                while (p) {
                    parentNames.unshift(p.name);
                    p = p.parent;
                }

                if (parentNames.length > 0) {
                    item.parentsInfo = '(' + parentNames.join(' > ') + ')';
                } else {
                    item.parentsInfo = '';
                }
            }

            return item.parentsInfo;
        }

        function initializeDropdownHandler() {
            $element.find('.input-text').focusin(function() {
                if (!$ctrl.dropdownVisible) {
                    toggleDropdown();
                    $scope.$digest();
                }
            });

            $element.focusout(function() {
                $timeout(function() {
                    var elementLostFocus = $element.has(':focus').length === 0;
                    if (elementLostFocus && $ctrl.dropdownVisible) {
                        toggleDropdown();
                    }
                });
            });

            $element.on('keydown', handleKeyDown);
        }

        //
        // Key interactions handlers
        //
        var KEY_ENTER = 13;
        var KEY_ESC = 27;
        var KEY_SPACE = 32;
        var KEY_LEFT_ARROW = 37;
        var KEY_UP_ARROW = 38;
        var KEY_RIGHT_ARROW = 39;
        var KEY_DOWN_ARROW = 40;
        var HANDLED_KEYS = [
            KEY_UP_ARROW,
            KEY_DOWN_ARROW,
            KEY_LEFT_ARROW,
            KEY_RIGHT_ARROW,
            KEY_ENTER,
            KEY_SPACE,
            KEY_ESC,
        ];

        function handleKeyDown(event) {
            if (
                !$ctrl.dropdownVisible ||
                HANDLED_KEYS.indexOf(event.keyCode) < 0
            )
                return;

            if (
                event.keyCode === KEY_UP_ARROW ||
                event.keyCode === KEY_DOWN_ARROW
            )
                handleBasicMovement(event);
            if (
                event.keyCode === KEY_LEFT_ARROW ||
                event.keyCode === KEY_RIGHT_ARROW
            )
                handleCollapse(event);
            if (event.keyCode === KEY_ENTER || event.keyCode === KEY_SPACE)
                toggleSelection($ctrl.highlightedItem);
            if (event.keyCode === KEY_ESC) toggleDropdown();

            event.preventDefault();
            event.stopPropagation();
            $scope.$digest();
        }

        function handleBasicMovement(event) {
            var lastIdx = $ctrl.filteredList.length - 1;
            var idx = $ctrl.filteredList.indexOf($ctrl.highlightedItem);
            if (event.keyCode === KEY_UP_ARROW)
                idx = idx <= 0 ? lastIdx : --idx;
            if (event.keyCode === KEY_DOWN_ARROW)
                idx = idx >= lastIdx ? 0 : ++idx;

            $ctrl.highlightedItem = $ctrl.filteredList[idx];
            scrollToItem($ctrl.highlightedItem);
        }

        function handleCollapse(event) {
            if ($ctrl.searchQuery) return;

            if (event.keyCode === KEY_LEFT_ARROW) {
                if (
                    $ctrl.highlightedItem.isCollapsed &&
                    $ctrl.highlightedItem.level === 1
                )
                    return;
                if ($ctrl.highlightedItem.isCollapsed)
                    $ctrl.highlightedItem = $ctrl.highlightedItem.parent;
                toggleCollapse($ctrl.highlightedItem);
            }

            if (
                event.keyCode === KEY_RIGHT_ARROW &&
                !$ctrl.highlightedItem.isLeaf
            ) {
                if ($ctrl.highlightedItem.isCollapsed) {
                    toggleCollapse($ctrl.highlightedItem);
                }
            }
        }

        function scrollToItem(item) {
            if (!item) return;

            // Scroll to item in case that is currently not shown
            // If it is lower in list scroll down so that it is displayed at the bottom,
            // otherwise scroll up to show it at the top.
            var $scrollContainer = $element.find('.scroll-container');
            var height = $scrollContainer.height();

            var idx = $ctrl.filteredList.indexOf(item);
            var selectedPos = idx * $ctrl.ITEM_HEIGHT;

            var viewFrom = $scrollContainer.scrollTop();
            var viewTo = viewFrom + height;

            if (selectedPos < viewFrom) {
                $scrollContainer.scrollTop(selectedPos);
            } else if (selectedPos >= viewTo) {
                $scrollContainer.scrollTop(
                    selectedPos - height + $ctrl.ITEM_HEIGHT
                );
            }
        }
    },
});
