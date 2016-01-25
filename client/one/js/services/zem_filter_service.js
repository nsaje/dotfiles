/* globals JSON */
"use strict";

oneApp.factory('zemFilterService', ['$location', function ($location) {
    // Because filteredSources is being watched (through getFilteredSources function) from
    // different controllers, it has to always point to the same array. Special care is taken
    // to never replace the reference (no assignments to this variable) so the array is
    // always modified in place.
    var filteredSources = [];
    var showArchived = false;
    var showBlacklistedPublisher = false;
    var blacklistedPublisherFilter = null;

    function init (user) {
        if ('zemauth.filter_sources' in user.permissions) {
            var filteredSourcesLocation = $location.search().filtered_sources;
            if (filteredSourcesLocation) {
            // replace the array in place
                Array.prototype.splice.apply(filteredSources, [0, filteredSources.length].concat(filteredSourcesLocation.split(',')));
            }
        }

        if ('zemauth.view_archived_entities' in user.permissions) {
            showArchived = $location.search().show_archived || false;
        }

        if ('zemauth.can_see_publishers' in user.permissions) {
            blacklistedPublisherFilter = $location.search().show_blacklisted_publishers || null;
        }
    }

    function setFilteredSourcesLocation () {
        if (filteredSources.length > 0) {
            $location.search('filtered_sources', filteredSources.join(','));
        } else {
            $location.search('filtered_sources', null);
        }
    }

    function setShowArchivedLocation () {
        if (showArchived) {
            $location.search('show_archived', showArchived);
        } else {
            $location.search('show_archived', null);
        }
    }

    function setBlacklistedPublishersLocation () {
        if (blacklistedPublisherFilter) {
            $location.search('show_blacklisted_publishers', blacklistedPublisherFilter);
        } else {
            $location.search('show_blacklisted_publishers', null);
        }
    }

    function getFilteredSources () {
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

    function isArchivedFilterOn () {
        return showArchived;
    }

    function isPublisherBlacklistFilterOn () {
        return blacklistedPublisherFilter !== null && blacklistedPublisherFilter !== 'all';
    }

    function isSourceFilterOn () {
        return filteredSources.length > 0;
    }

    function addFilteredSource (sourceId) {
        if (filteredSources.indexOf(sourceId) === -1) {
            filteredSources.push(sourceId);
            filteredSources.sort(function (a, b) { return parseInt(a) - parseInt(b); });
        }

        setFilteredSourcesLocation();
    }

    function removeFilteredSource (sourceId) {
        var ix = filteredSources.indexOf(sourceId);
        if (ix > -1) {
            filteredSources.splice(ix, 1);
        }

        setFilteredSourcesLocation();
    }

    function exclusivelyFilterSource (sourceId) {
        filteredSources.splice(0, filteredSources.length, sourceId);

        setFilteredSourcesLocation();
    }

    function removeFiltering () {
        filteredSources.splice(0, filteredSources.length);

        setFilteredSourcesLocation();
        setShowArchivedLocation();

        blacklistedPublisherFilter = null;
        setBlacklistedPublishers(null);
    }

    function getShowArchived () {
        return showArchived;
    }

    function setShowArchived (newValue) {
        showArchived = newValue;
        setShowArchivedLocation();
    }

    function getBlacklistedPublishers () {
        return blacklistedPublisherFilter;
    }

    function setBlacklistedPublishers (newValue) {
        blacklistedPublisherFilter = newValue;
        setBlacklistedPublishersLocation();
    }

    function getShowBlacklistedPublishers () {
        return showBlacklistedPublisher;
    }

    function setShowBlacklistedPublishers (newValue) {
        showBlacklistedPublisher = newValue;
    }

    return {
        init: init,
        isArchivedFilterOn: isArchivedFilterOn,
        getShowArchived: getShowArchived,
        setShowArchived: setShowArchived,
        getFilteredSources: getFilteredSources,
        isSourceFiltered: isSourceFiltered,
        isSourceFilterOn: isSourceFilterOn,
        addFilteredSource: addFilteredSource,
        exclusivelyFilterSource: exclusivelyFilterSource,
        removeFilteredSource: removeFilteredSource,
        removeFiltering: removeFiltering,
        isPublisherBlacklistFilterOn: isPublisherBlacklistFilterOn,
        getBlacklistedPublishers: getBlacklistedPublishers,
        setBlacklistedPublishers: setBlacklistedPublishers,
        getShowBlacklistedPublishers: getShowBlacklistedPublishers,
        setShowBlacklistedPublishers: setShowBlacklistedPublishers
    };
}]);
