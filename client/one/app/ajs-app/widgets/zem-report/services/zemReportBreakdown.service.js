angular
    .module('one.widgets')
    .service('zemReportBreakdownService', function(zemGridEndpointBreakdowns) {
        // eslint-disable-line max-len

        // Public API
        this.getAvailableBreakdowns = getAvailableBreakdowns;

        function getAvailableBreakdowns(breakdown, metaData) {
            var availableBreakdowns = [];

            var structureBreakdowns = getReportStructureBreakdowns(metaData);
            for (var i = 0; i < structureBreakdowns.length; i++) {
                var dimension = structureBreakdowns[i];
                if (!isInBreakdown(breakdown, dimension)) {
                    availableBreakdowns.push(dimension);
                }
            }

            if (!timeInBreakdown(breakdown)) {
                availableBreakdowns = availableBreakdowns.concat(
                    zemGridEndpointBreakdowns.TIME_BREAKDOWNS
                );
            }

            if (!deliveryInBreakdown(breakdown)) {
                availableBreakdowns = availableBreakdowns.concat(
                    zemGridEndpointBreakdowns.DELIVERY_BREAKDOWNS
                );
            }

            return availableBreakdowns;
        }

        function timeInBreakdown(breakdown) {
            zemGridEndpointBreakdowns.TIME_BREAKDOWNS.some(function(element) {
                return isInBreakdown(breakdown, element);
            });
        }

        function deliveryInBreakdown(breakdown) {
            zemGridEndpointBreakdowns.DELIVERY_BREAKDOWNS.some(function(
                element
            ) {
                return isInBreakdown(breakdown, element);
            });
        }

        function isInBreakdown(breakdown, dimension) {
            for (var i = 0; i < breakdown.length; i++) {
                if (breakdown[i].report_query === dimension.report_query) {
                    return true;
                }
            }
            return false;
        }

        function getReportStructureBreakdowns(metaData) {
            var entityBreakdown = zemGridEndpointBreakdowns.getEntityLevelBreakdown(
                metaData.level
            );
            var structureBreakdowns = zemGridEndpointBreakdowns.ENTITY_BREAKDOWNS.slice(
                zemGridEndpointBreakdowns.ENTITY_BREAKDOWNS.indexOf(
                    entityBreakdown
                ) + 1
            );

            if (metaData.breakdown !== entityBreakdown.query) {
                structureBreakdowns.unshift(entityBreakdown);
            } else {
                structureBreakdowns.push(
                    zemGridEndpointBreakdowns.BREAKDOWNS.source
                );
            }

            if (
                metaData.breakdown === constants.breakdown.PUBLISHER &&
                structureBreakdowns.length > 0 &&
                structureBreakdowns[structureBreakdowns.length - 1].query ===
                    constants.breakdown.CONTENT_AD
            ) {
                structureBreakdowns.pop();
            }

            return structureBreakdowns;
        }
    });
