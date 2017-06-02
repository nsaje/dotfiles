angular.module('one.widgets').component('zemTreeSelect', {
    bindings: {
        rootNode: '<',
        initialSelection: '<',
        onUpdate: '&',
    },
    templateUrl: '/app/common/components/zem-tree-select/zemTreeSelect.component.html',
    controller: function ($scope, $element, $timeout, zemTreeSelectService) {
        //
        // Tree Node (input: $ctrl.rootNode)
        //  - name, id, value
        //  - navigationOnly (default - false)
        //  - childNodes: [nodes]
        //

        var $ctrl = this;
        $ctrl.toggleItemState = toggleItemState;
        $ctrl.toggleCollapse = toggleCollapse;
        $ctrl.toggleSelection = toggleSelection;
        $ctrl.onSearch = onSearch;
        $ctrl.highlightItem = highlightItem;
        $ctrl.getParentsInfo = getParentsInfo;

        $ctrl.$onInit = function () {
            $ctrl.list = zemTreeSelectService.createList($ctrl.rootNode);
            $ctrl.filteredList = zemTreeSelectService.filterList($ctrl.list);
            highlightItem($ctrl.filteredList[0]);
            initializeSelection();
            initializeDropdownHandler();
        };

        function initializeSelection () {
            if (!$ctrl.initialSelection) return;

            var mapIds = {};
            $ctrl.list.forEach(function (node) { mapIds[node.id.toString()] = node; });
            $ctrl.initialSelection.forEach(function (id) {
                mapIds[id].selected = true;
            });

            $ctrl.selectedItems = $ctrl.list.filter(function (item) { return item.selected; });
        }

        function toggleDropdown () {
            if ($ctrl.dropdownVisible) {
                $ctrl.dropdownVisible = false;
                $ctrl.searchQuery = '';
            } else {
                $ctrl.dropdownVisible = true;
            }
        }

        function onSearch (searchQuery) {
            $ctrl.filteredList = zemTreeSelectService.filterList($ctrl.list, searchQuery);
        }

        function toggleCollapse (category) {
            category.isCollapsed = !category.isCollapsed;
            $ctrl.filteredList = zemTreeSelectService.filterList($ctrl.list);
        }

        function toggleItemState (item) {
            if (item.isLeaf || $ctrl.searchQuery) {
                toggleSelection(item);
            } else {
                toggleCollapse(item);
            }
        }

        function toggleSelection (item) {
            if (!item.isSelectable) return;
            item.selected = !item.selected;
            updateSelection();
        }

        function updateSelection () {
            $ctrl.selectedItems = $ctrl.list.filter(function (item) { return item.selected; });
            $ctrl.onUpdate({nodes: $ctrl.selectedItems.map(function (item) { return item.value.id; })});
        }

        function highlightItem (item) {
            $ctrl.highlightedItem = item;
        }

        function getParentsInfo (item) {
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

        function initializeDropdownHandler () {
            $element.focusin(function () {
                if (!$ctrl.dropdownVisible) {
                    toggleDropdown();
                    $scope.$digest();
                }
            });

            $element.focusout(function () {
                $timeout(function () {
                    var elementLostFocus  = $element.has(':focus').length === 0;
                    if (elementLostFocus && $ctrl.dropdownVisible) {
                        toggleDropdown();
                    }
                });
            });

            $element.on('keydown', function closeMenu (e) {
                if (e.which === 27) { // ESC
                    if ($ctrl.dropdownVisible) {
                        toggleDropdown();
                        e.stopPropagation();

                        $scope.$digest();
                    }
                }
            });
        }
    }
});
