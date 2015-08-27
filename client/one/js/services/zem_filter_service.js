/* globals JSON */
"use strict"

oneApp.factory('zemFilterService', ['$location', function($location) {
    // Because filteredSoruces is being watched (through getFilteredSources function) from
    // different controllers, it has to always point to the same array. Special care is taken
    // to never replace the reference (no assignments to this variable) so the array is
    // always modified in place.
    var filteredSources = [];
    var showArchived = false;

    function init(user) {
        if ('zemauth.filter_sources' in user.permissions) {
            var filteredSourcesLocation = $location.search().filtered_sources;
            if (filteredSourcesLocation) {
            // replace the array in place
                Array.prototype.splice.apply(filteredSources, [0, filteredSources.length].concat(filteredSourcesLocation.split(',')));
            }
        }

        if ('zemauth.view_archived_entities' in user.permissions) {
            if ($location.search().show_archived == "1") {
                showArchived = true;
            }
        }
   }

    function setFilteredSourcesLocation() {
        if (filteredSources.length > 0) {
            $location.search('filtered_sources', filteredSources.join(','));
        } else {
            $location.search('filtered_sources', null);
        }
    }

    function setShowArchivedLocation() {
        if (showArchived) {
            $location.search('show_archived', 1);
        } else {
            $location.search('show_archived', null);
        }
    }

    function getFilteredSources() {
        return filteredSources;
    }

    function isSourceFiltered (sourceId) {
        for (var i = 0; i < filteredSources.length; i++) {
            if (filteredSources[i] === sourceId) {
                return true;
            }
        }

        return false;
    }

    function isSourceFilterOn () {
        return filteredSources.length > 0;
    }

    function addFilteredSource(sourceId) {
        if (filteredSources.indexOf(sourceId) === -1) {
            filteredSources.push(sourceId);
            filteredSources.sort(function (a, b) { return parseInt(a) - parseInt(b); });
        }

        setFilteredSourcesLocation();
    }

    function removeFilteredSource(sourceId) {
        var ix = filteredSources.indexOf(sourceId);
        if (ix > -1) {
            filteredSources.splice(ix, 1);
        }

        setFilteredSourcesLocation();
    }

    function exclusivelyFilterSource(sourceId) {
        filteredSources.splice(0, filteredSources.length, sourceId);

        setFilteredSourcesLocation();
    }

    function removeFiltering() {
        filteredSources.splice(0, filteredSources.length);

        setFilteredSourcesLocation();
        setShowArchivedLocation();
    }

    function getShowArchived() {
        return showArchived;
    }

    function setShowArchived(newValue) {
        showArchived = newValue;

        setShowArchivedLocation();
    }

    return {
        init: init,
        getShowArchived: getShowArchived,
        setShowArchived: setShowArchived,
        getFilteredSources: getFilteredSources,
        isSourceFiltered: isSourceFiltered,
        isSourceFilterOn: isSourceFilterOn,
        addFilteredSource: addFilteredSource,
        exclusivelyFilterSource: exclusivelyFilterSource,
        removeFilteredSource: removeFilteredSource,
        removeFiltering: removeFiltering
    };
}]);
