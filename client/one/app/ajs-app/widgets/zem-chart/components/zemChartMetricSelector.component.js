var arrayHelpers = require('../../../../shared/helpers/array.helpers');
var CategoryName = require('../../../../app.constants').CategoryName;

angular.module('one.widgets').component('zemChartMetricSelector', {
    bindings: {
        metric: '<',
        metricOptions: '<',
        nullable: '<',
        onMetricChanged: '&',
    },
    template: require('./zemChartMetricSelector.component.html'),
    controller: function(zemCostModeService, zemAuthStore) {
        var $ctrl = this;

        $ctrl.categoryName = CategoryName;
        $ctrl.isDropdownOpen = false;
        $ctrl.hasPermission = zemAuthStore.hasPermission.bind(zemAuthStore);
        $ctrl.$onInit = function() {
            zemCostModeService.onCostModeUpdate(function() {
                $ctrl.categories = getCategories($ctrl.metricOptions);
            });
        };

        $ctrl.$onChanges = function(changes) {
            if (changes.metricOptions) {
                $ctrl.categories = getCategories($ctrl.metricOptions);
            }
        };

        function getCategoryColumns(category) {
            var costMode = zemCostModeService.getCostMode();

            return category.metrics.filter(function(metric) {
                if (zemCostModeService.isTogglableCostMode(metric.costMode))
                    return metric.costMode === costMode;
                return true;
            });
        }

        function getCategory(category) {
            var categoryColumns = getCategoryColumns(category),
                subcategories = [];

            if (category.hasOwnProperty('subcategories')) {
                subcategories = category.subcategories.map(function(
                    subcategory
                ) {
                    return getCategory(subcategory);
                });
            }

            return {
                name: category.name,
                description: category.description,
                subcategories: subcategories,
                metrics: categoryColumns,
                isNewFeature: category.isNewFeature,
                helpText: category.helpText,
            };
        }

        function getCategories(metricOptions) {
            var categories = [];
            if (!arrayHelpers.isEmpty(metricOptions)) {
                metricOptions.forEach(function(metricOption) {
                    var category = getCategory(metricOption);
                    if (
                        category.metrics.length > 0 ||
                        category.subcategories.length > 0
                    ) {
                        categories.push(category);
                    }
                });
            }
            return categories;
        }

        $ctrl.onChanged = function(metric) {
            $ctrl.onMetricChanged({value: metric});
        };
    },
});
