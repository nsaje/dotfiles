angular
    .module('one.widgets')
    .service('zemReportBreakdownService', function(zemGridEndpointBreakdowns) {
        // eslint-disable-line max-len

        // Public API
        this.getAvailableBreakdowns = getAvailableBreakdowns;

        function getAvailableBreakdowns(breakdown, metaData) {
            var availableBreakdowns = [];
            var disabledDeliveryBreakdowns = [
                'age',
                'gender',
                'age_gender',
                'zem_placement_type',
                'video_playback_method',
            ];

            var structureBreakdowns = getReportStructureBreakdowns(metaData);
            structureBreakdowns.forEach(function(dimension) {
                if (!isInBreakdown(breakdown, dimension)) {
                    availableBreakdowns.push(
                        Object.assign({}, dimension, {
                            breakdownType: 'Structure',
                        })
                    );
                }
            });

            if (!timeInBreakdown(breakdown)) {
                availableBreakdowns = availableBreakdowns.concat(
                    zemGridEndpointBreakdowns.TIME_BREAKDOWNS.map(function(
                        dimension
                    ) {
                        return Object.assign({}, dimension, {
                            breakdownType: 'Time',
                        });
                    })
                );
            }

            if (!deliveryInBreakdown(breakdown)) {
                availableBreakdowns = availableBreakdowns.concat(
                    zemGridEndpointBreakdowns.DELIVERY_BREAKDOWNS.filter(
                        function(dimension) {
                            return !disabledDeliveryBreakdowns.includes(
                                dimension.query
                            );
                        }
                    ).map(function(dimension) {
                        return Object.assign({}, dimension, {
                            breakdownType: 'Delivery',
                        });
                    })
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
