angular.module('one.widgets').component('zemChartMetricSelector', {
    bindings: {
        chart: '<',
        metric: '<',
        nullable: '<',
        onMetricChanged: '&',
    },
    template: require('./zemChartMetricSelector.component.html'),
    controller: function(
        zemCostModeService,
        zemNavigationNewService,
        zemPermissions
    ) {
        var $ctrl = this;

        $ctrl.hasPermission = zemPermissions.hasPermission;
        $ctrl.$onInit = function() {
            initializeCategories();
            zemCostModeService.onCostModeUpdate(initializeCategories);
            zemNavigationNewService.onUsesBCMv2Update(initializeCategories);
            $ctrl.chart.metrics.metaData.onMetricsUpdated(initializeCategories);
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
            };
        }

        function initializeCategories() {
            $ctrl.categories = [];
            $ctrl.chart.metrics.options.forEach(function(category) {
                var newCategory = getCategory(category);
                if (
                    newCategory.metrics.length > 0 ||
                    newCategory.subcategories.length > 0
                ) {
                    $ctrl.categories.push(newCategory);
                }
            });
        }

        $ctrl.onChanged = function(metric) {
            $ctrl.onMetricChanged({value: metric});
        };
    },
});
