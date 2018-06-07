require('./zemFilterSelector.component.less');

angular.module('one.widgets').component('zemFilterSelector', {
    template: require('./zemFilterSelector.component.html'),
    controller: function ($element, $timeout, zemDataFilterService, zemFilterSelectorService, zemFilterSelectorSharedService, zemPermissions) { // eslint-disable-line max-len
        var $ctrl = this;

        $ctrl.isPermissionInternal = zemPermissions.isPermissionInternal;
        $ctrl.isExpanded = zemFilterSelectorSharedService.isSelectorExpanded;
        $ctrl.removeCondition = zemFilterSelectorService.removeAppliedCondition;
        $ctrl.clearFilter = zemDataFilterService.resetAllConditions;
        $ctrl.toggleSelectAll = zemFilterSelectorService.toggleSelectAll;
        $ctrl.applyFilter = applyFilter;
        $ctrl.closeFilter = zemFilterSelectorSharedService.toggleSelector;
        $ctrl.getVisibleSectionsClasses = getVisibleSectionsClasses;
        $ctrl.scrollAppliedConditionsList = scrollAppliedConditionsList;

        var listContainerElement;
        var listElement;
        var listElementWidth;
        var selectionUpdateHandler;
        var dataFilterUpdateHandler;

        $ctrl.$onInit = function () {
            zemFilterSelectorService.init();

            selectionUpdateHandler = zemFilterSelectorService.onSectionsUpdate(function () {
                refresh();
                updateListElementWidth();
            });
            dataFilterUpdateHandler = zemDataFilterService.onDataFilterUpdate(function () {
                refresh();
                updateListElementWidth();
            });

            $ctrl.appliedConditions = zemFilterSelectorService.getAppliedConditions();
            $ctrl.visibleSections = zemFilterSelectorService.getVisibleSections();
            $ctrl.isListElementOverflowing = false;

            refresh();
            updateListElementWidth();
        };

        $ctrl.$onDestroy = function () {
            if (selectionUpdateHandler) selectionUpdateHandler();
            if (dataFilterUpdateHandler) dataFilterUpdateHandler();
        };

        $ctrl.$postLink = function () {
            listContainerElement = $element.find('.applied-conditions__list-container');
            listElement = $element.find('.applied-conditions__list');
        };

        function applyFilter () {
            zemFilterSelectorService.applyFilter($ctrl.visibleSections);
            zemFilterSelectorSharedService.toggleSelector();
            setListElementTranslateX(0);
        }

        function getVisibleSectionsClasses () {
            var classes = '';
            $ctrl.visibleSections.forEach(function (section) {
                classes += 'filter-sections--visible-' + section.cssClass + ' ';
            });
            return classes;
        }

        var STEP_WIDTH = 300;
        function scrollAppliedConditionsList (direction) {
            // Parse element's translateX property
            var matrix = listElement.css('transform').replace(/[^0-9\-.,]/g, '').split(',');
            var x = Math.floor(matrix[12]) || Math.floor(matrix[4]);

            if (direction === 'left') {
                x = (x + STEP_WIDTH) < 0 ? (x + STEP_WIDTH) : 0;
            } else if (direction === 'right') {
                var minX = -(listElementWidth - listContainerElement.width());
                x = (x - STEP_WIDTH) >= minX ? (x - STEP_WIDTH) : minX;
            }

            setListElementTranslateX(x);
        }

        function calculateListElementWidth (children) {
            var width = 0;
            for (var i = 0; i < children.length; i++) {
                width += $(children[i]).outerWidth(true);
            }
            return width;
        }

        function updateListElementWidth () {
            $timeout(function () {
                listElementWidth = calculateListElementWidth(listElement.find('.applied-conditions__condition'));
                listElement.width(listElementWidth + 'px');

                $ctrl.isListElementOverflowing = listElementWidth > listContainerElement.width();
                if (!$ctrl.isListElementOverflowing) {
                    setListElementTranslateX(0);
                }
            }, 0);
        }

        function setListElementTranslateX (x) {
            var translateCssProperty = 'translateX(' + x + 'px)';
            listElement.css('transform', translateCssProperty);
        }

        function refresh () {
            $ctrl.appliedConditions = zemFilterSelectorService.getAppliedConditions();
            $ctrl.visibleSections = zemFilterSelectorService.getVisibleSections();

            // Add or remove data-filter-enabled class to body to enable global desing changes if data filter is enabled
            if ($ctrl.appliedConditions.length) {
                $('body').addClass('data-filter-enabled');
            } else {
                $('body').removeClass('data-filter-enabled');
            }
        }
    },
});
