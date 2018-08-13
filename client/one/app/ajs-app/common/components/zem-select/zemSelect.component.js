require('./zemSelect.component.less');

angular.module('one.common').component('zemSelect', {
    bindings: {
        selectedId: '<',
        onSelect: '&',
        store: '<',
        texts: '<',
    },
    template: require('./zemSelect.component.html'),
    controller: function(
        $scope,
        $element,
        $timeout,
        hotkeys,
        zemSelectList,
        zemUtils
    ) {
        var KEY_UP_ARROW = 38;
        var KEY_DOWN_ARROW = 40;
        var KEY_ENTER = 13;

        var ITEM_HEIGHT_DEFAULT = 30; // NOTE: Change in CSS too!

        var $ctrl = this;

        //
        // Template methods and variables
        //

        $ctrl.onSearch = onSearch;
        $ctrl.onItemClick = onItemClick;
        $ctrl.toggleHighlighted = toggleHighlighted;
        $ctrl.getItemHeight = getItemHeight;
        $ctrl.getItemClasses = getItemClasses;

        $ctrl.selected = null;
        $ctrl.highlighted = null;

        $ctrl.$onInit = function() {
            initializeSelection();
            initializeDropdownHandler();
        };

        $ctrl.$onDestroy = function() {
            $element.unbind();
        };

        function initializeSelection() {
            filterList('').then(function() {
                if ($ctrl.selectedId) {
                    for (var i = 0; i < $ctrl.list.items.length; i++) {
                        if ($ctrl.list.items[i].id === $ctrl.selectedId) {
                            selectItem($ctrl.list.items[i]);
                            break;
                        }
                    }
                }
            });
        }

        function initializeDropdownHandler() {
            $element.keydown(function(event) {
                if (!$ctrl.list) return;
                if (event.keyCode === KEY_UP_ARROW) upSelection(event);
                if (event.keyCode === KEY_DOWN_ARROW) downSelection(event);
                if (event.keyCode === KEY_ENTER) enterSelection(event);
                $scope.$digest();
            });

            $element.on('click', function() {
                $timeout(function() {
                    if (!$ctrl.dropdownVisible) {
                        openDropdown(true);
                    }
                });
            });

            $element.focusout(function(event) {
                if (event.target === getSelectedLabelElement()) {
                    return;
                }
                $timeout(function() {
                    var elementLostFocus = $element.has(':focus').length === 0;
                    if (elementLostFocus && $ctrl.dropdownVisible) {
                        closeDrowdown();
                    }
                });
            });
        }

        function getItemHeight() {
            return ITEM_HEIGHT_DEFAULT;
        }

        function closeDrowdown() {
            $ctrl.dropdownVisible = false;
            $timeout(function() {
                focusSelected();
            });
        }

        function openDropdown(timeout) {
            $ctrl.dropdownVisible = true;

            if (timeout) {
                $timeout(function() {
                    focusInput();
                    scrollToItem($ctrl.highlighted, true);
                });
            } else {
                focusInput();
                scrollToItem($ctrl.highlighted, true);
            }
        }

        function onItemClick(item) {
            if (item.isHeader) return;

            selectItem(item);
            closeDrowdown();
        }

        function toggleHighlighted(item) {
            if (item.isHeader) return;
            $ctrl.highlighted = item;
        }

        function selectItem(item) {
            $ctrl.selected = item;
            $ctrl.highlighted = item;
            $ctrl.onSelect({item: $ctrl.selected});
        }

        function onSearch(searchQuery) {
            if (!$ctrl.dropdownVisible) openDropdown();
            filterList(searchQuery);
        }

        function filterList(searchQuery) {
            if ($ctrl.previousPromise) {
                $ctrl.previousPromise.abort();
            }

            var deferred = zemUtils.createAbortableDefer();

            $ctrl.store.search(searchQuery).then(function(items) {
                deferred.resolve(items);
            });

            $ctrl.previousPromise = deferred.promise;

            return deferred.promise.then(function(items) {
                $ctrl.list = zemSelectList.createInstance(items);
            });
        }

        function upSelection(event) {
            event.preventDefault();

            if ($ctrl.dropdownVisible) {
                // highlight item above
                var idx = $ctrl.list.indexOf($ctrl.highlighted);
                $ctrl.highlighted = $ctrl.list.previous(idx);
                if (!$ctrl.highlighted) {
                    $ctrl.highlighted = $ctrl.list.last();
                }
                scrollToItem($ctrl.highlighted);
            } else {
                $ctrl.highlighted = $ctrl.selected || $ctrl.list.last();
                openDropdown(true);
            }
        }

        function downSelection(event) {
            event.preventDefault();

            if ($ctrl.dropdownVisible) {
                // highlight item below
                var idx = $ctrl.list.indexOf($ctrl.highlighted);
                $ctrl.highlighted = $ctrl.list.next(idx);
                if (!$ctrl.highlighted) {
                    $ctrl.highlighted = $ctrl.list.first();
                }
                scrollToItem($ctrl.highlighted);
            } else {
                $ctrl.highlighted = $ctrl.selected || $ctrl.list.first();
                openDropdown(true);
            }
        }

        function enterSelection() {
            if (!$ctrl.dropdownVisible) {
                openDropdown();
            } else {
                // dropdown is opened, select item
                var item = $ctrl.highlighted;
                if (!item && $ctrl.searchQuery.length > 0) {
                    // If searching select first item if no selection has been made
                    item = $ctrl.list.first();
                }

                selectItem(item);
                closeDrowdown();
            }
        }

        function scrollToItem(item, scrollToMiddleIfOutside) {
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
                $scrollContainer.scrollTop(
                    selectedPos -
                        height +
                        getItemHeight($ctrl.list.getItem(idx))
                );
            }
        }

        function focusInput() {
            $timeout(function() {
                getInputElement().focus();
            });
        }

        function focusSelected() {
            $timeout(function() {
                getSelectedLabelElement().focus();
            });
        }

        function getInputElement() {
            return $element.find('input')[0];
        }

        function getSelectedLabelElement() {
            return $element.find('#selected-item-label')[0];
        }

        function getItemClasses(item) {
            var classes = ['zem-select-dropdown-item__name'];
            if (item.isH1) classes.push('zem-select-dropdown-item__name--h1');
            if (item.isH2) classes.push('zem-select-dropdown-item__name--h2');
            return classes;
        }
    },
});
