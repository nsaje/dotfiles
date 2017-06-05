angular.module('one.widgets').component('zemSelect', {
    bindings: {
        selectedId: '<',
        onSelect: '&',
        store: '<',
        texts: '<',
    },
    templateUrl: '/app/common/components/zem-select/zemSelect.component.html',
    controller: function ($scope, $element, $timeout, hotkeys, zemSelectList, zemUtils) {
        var KEY_UP_ARROW = 38;
        var KEY_DOWN_ARROW = 40;
        var KEY_ENTER = 13;

        var ITEM_HEIGHT_DEFAULT = 30; // NOTE: Change in CSS too!

        var $ctrl = this;

        //
        // Template methods and variables
        //

        $ctrl.search = search;
        $ctrl.focus = focus;
        $ctrl.toggleSelection = toggleSelection;
        $ctrl.toggleHighlighted = toggleHighlighted;
        $ctrl.getItemHeight = getItemHeight;
        $ctrl.getItemClasses = getItemClasses;

        $ctrl.selected = null;

        $ctrl.$onInit = function () {
            $element.keydown(handleKeyDown);
            $ctrl.search('', function () {
                $timeout(function () {
                    if ($ctrl.selectedId) {

                        // init selected based on id
                        for (var i = 0; i < $ctrl.list.items.length; i++) {
                            if ($ctrl.list.items[i].id === $ctrl.selectedId) {
                                $ctrl.selected = $ctrl.list.items[i];
                                break;
                            }
                        }

                        selectItem($ctrl.selected);
                        scrollToItem($ctrl.selected, true);
                    }
                });
            });
        };

        $ctrl.$onDestroy = function () {
            $element.unbind();
        };

        function getItemHeight () {
            return ITEM_HEIGHT_DEFAULT;
        }

        function focus () {
            if (!$ctrl.dropdownVisible) openDropdown();
        }

        function closeDrowdown () {
            $ctrl.dropdownVisible = false;
            $ctrl.highlighted = $ctrl.selected;
        }

        function openDropdown () {
            $ctrl.dropdownVisible = true;
            $ctrl.highlighted = $ctrl.selected;

            // Close dropdown when user clicks outside of this element
            angular.element(document).one('click', function closeMenu (e) {
                if ($element.has(e.target).length === 0) {
                    // Use $timeout to make sure that this happens inside $digest loop
                    $timeout(closeDrowdown);
                } else {
                    angular.element(document).one('click', closeMenu);
                }
            });
        }

        function toggleSelection (item) {
            if (item.isHeader) return;

            if ($ctrl.selected === item) {
                unselectItem();
            } else {
                selectItem(item);
                closeDrowdown();
            }
        }

        function toggleHighlighted (item) {
            if (item.isHeader) return;
            $ctrl.highlighted = item;
        }

        function unselectItem () {
            $ctrl.selected = null;
            $ctrl.onSelect({'item': $ctrl.selected});
        }

        function selectItem (item) {
            $ctrl.selected = item;
            $ctrl.onSelect({'item': $ctrl.selected});

            $ctrl.searchQuery = item.name;
        }

        function search (searchQuery, locatedFn) {
            if (!$ctrl.dropdownVisible) openDropdown();

            if ($ctrl.previousPromise) {
                $ctrl.previousPromise.abort();
            }

            var deferred = zemUtils.createAbortableDefer();

            $ctrl.store.search(searchQuery).then(function (items) {
                deferred.resolve(items);
            });

            deferred.promise.then(function (items) {
                $ctrl.list = zemSelectList.createInstance(items);
                if (locatedFn) locatedFn();
            });

            $ctrl.previousPromise = deferred.promise;
        }

        function handleKeyDown (event) {
            if (!$ctrl.list) return;
            if (event.keyCode === KEY_UP_ARROW) upSelection(event);
            if (event.keyCode === KEY_DOWN_ARROW) downSelection(event);
            if (event.keyCode === KEY_ENTER) enterSelection(event);
            $scope.$digest();
        }

        function upSelection (event) {
            event.preventDefault();

            if ($ctrl.dropdownVisible) {
                // highlight item above
                var idx = $ctrl.list.indexOf($ctrl.highlighted);
                $ctrl.highlighted = $ctrl.list.previous(idx);
                if (!$ctrl.highlighted) {
                    $ctrl.highlighted = $ctrl.list.last();
                }
            } else {
                $ctrl.highlighted = $ctrl.selected || $ctrl.list.last();
                openDropdown();
            }

            scrollToItem($ctrl.highlighted);
        }

        function downSelection (event) {
            event.preventDefault();

            if ($ctrl.dropdownVisible) {
                // highlight item below
                var idx = $ctrl.list.indexOf($ctrl.highlighted);
                $ctrl.highlighted = $ctrl.list.next(idx);
                if (!$ctrl.highlighted) {
                    $ctrl.highlighted = $ctrl.list.first();
                }
            } else {
                $ctrl.highlighted = $ctrl.selected || $ctrl.list.first();
                openDropdown();
            }

            scrollToItem($ctrl.highlighted);
        }

        function enterSelection () {
            if (!$ctrl.dropdownVisible) return openDropdown();

            var item = $ctrl.highlighted;
            if (!item && $ctrl.searchQuery.length > 0) {
                // If searching select first item if no selection has been made
                item = $ctrl.list.first();
            }

            selectItem(item);
            closeDrowdown();
        }

        function scrollToItem (item, scrollToMiddleIfOutside) {
            if (!item) return;

            // Scroll to item in case that is currently not shown
            // If it is lower in list scroll down so that it is displayed at the bottom,
            // otherwise scroll up to show it at the top.
            var $scrollContainer = $element.find('.scroll-container');
            var height = $scrollContainer.height();

            var selectedPos = 0;
            var idx = $ctrl.list.indexOf(item);
            for (var i = 0; i < idx; i++) {
                selectedPos += getItemHeight($ctrl.list.getItem(i));
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
                $scrollContainer.scrollTop(selectedPos - height + getItemHeight($ctrl.list.getItem(idx)));
            }
        }

        function getItemClasses (item) {
            var classes = ['zem-select-dropdown-item__name'];
            if (item.isH1) classes.push('zem-select-dropdown-item__name--h1');
            if (item.isH2) classes.push('zem-select-dropdown-item__name--h2');
            return classes;
        }
    }
});
