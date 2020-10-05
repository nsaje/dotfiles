require('./zemGridBreakdownSelector.component.less');

angular.module('one.widgets').component('zemGridBreakdownSelector', {
    bindings: {
        api: '=',
    },
    template: require('./zemGridBreakdownSelector.component.html'),
    controller: function() {
        var $ctrl = this;

        $ctrl.onChecked = onChecked;
        $ctrl.applyBreakdown = applyBreakdown;

        $ctrl.$onInit = function() {
            initializeSelector();
            $ctrl.api.onMetaDataUpdated(null, initializeSelector);
        };

        function initializeSelector() {
            // Skip base level breakdown selection
            $ctrl.breakdownGroups = [
                $ctrl.api.getMetaData().breakdownGroups.structure,
                $ctrl.api.getMetaData().breakdownGroups.delivery,
                $ctrl.api.getMetaData().breakdownGroups.time,
            ].filter(function(group) {
                return group.available !== false;
            });

            setDefaultBreakdowns(
                constants.level.ACCOUNTS,
                constants.breakdown.CAMPAIGN,
                [constants.breakdown.AD_GROUP]
            );
        }

        function setDefaultBreakdowns(level, breakdown, defaultBreakdowns) {
            // Set which breakdowns to load by default for different level/breakdown combinations
            var metaData = $ctrl.api.getMetaData();
            if (metaData.level === level && metaData.breakdown === breakdown) {
                $ctrl.breakdownGroups.forEach(function(group) {
                    group.breakdowns.forEach(function(b) {
                        if (defaultBreakdowns.indexOf(b.query) !== -1) {
                            b.checked = true;
                            onChecked(b, group);
                        }
                    });
                });
                $ctrl.applyBreakdown();
            }
        }

        function onChecked(breakdown, group) {
            if (breakdown.checked) {
                group.breakdowns.forEach(function(b) {
                    if (b !== breakdown) b.checked = false;
                });
            }
        }

        function applyBreakdown() {
            // Add base level breakdown and all checked
            // breakdowns in successive levels
            var breakdown = [];
            var baseLevelGroup = $ctrl.api.getMetaData().breakdownGroups.base;
            breakdown.push(baseLevelGroup.breakdowns[0]);
            $ctrl.breakdownGroups.forEach(function(group) {
                group.breakdowns.forEach(function(b) {
                    if (b.checked) breakdown.push(b);
                });
            });
            $ctrl.api.setBreakdown(breakdown, true);
        }
    },
});
