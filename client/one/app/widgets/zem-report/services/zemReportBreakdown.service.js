angular.module('one.widgets').service('zemReportBreakdownService', function (zemGridEndpointBreakdowns) {  // eslint-disable-line max-len

    // Public API
    this.getAvailableBreakdowns = getAvailableBreakdowns;

    function getAvailableBreakdowns (breakdown, metaData) {
        var availableBreakdowns = [];

        var structureBreakdowns = getReportStructureBreakdowns(metaData);
        for (var i = 0; i < structureBreakdowns.length; i++) {
            var dimension = structureBreakdowns[i];
            if (!isInBreakdown(breakdown, dimension)) {
                availableBreakdowns.push(dimension);
            }
        }

        if (!timeInBreakdown(breakdown)) {
            availableBreakdowns = availableBreakdowns.concat(zemGridEndpointBreakdowns.TIME_BREAKDOWNS);
        }

        return availableBreakdowns;
    }

    function timeInBreakdown (breakdown) {
        for (var i = 0; i < zemGridEndpointBreakdowns.TIME_BREAKDOWNS.length; i++) {
            if (isInBreakdown(breakdown, zemGridEndpointBreakdowns.TIME_BREAKDOWNS[i])) {
                return true;
            }
        }
        return false;
    }

    function isInBreakdown (breakdown, dimension) {
        for (var i = 0; i < breakdown.length; i++) {
            if (breakdown[i].report_query === dimension.report_query) {
                return true;
            }
        }
        return false;
    }

    function getReportStructureBreakdowns (metaData) {
        if (metaData.breakdown === constants.breakdown.PUBLISHER) {
            return [];
        }

        var entityBreakdown = zemGridEndpointBreakdowns.getEntityLevelBreakdown(metaData.level);
        var structureBreakdowns = zemGridEndpointBreakdowns.ENTITY_BREAKDOWNS.slice(
            zemGridEndpointBreakdowns.ENTITY_BREAKDOWNS.indexOf(entityBreakdown) + 1
        );

        if (metaData.breakdown === constants.breakdown.MEDIA_SOURCE) {
            structureBreakdowns.unshift(entityBreakdown);
        } else {
            structureBreakdowns.push(zemGridEndpointBreakdowns.BREAKDOWNS.source);
        }

        return structureBreakdowns;
    }
});
