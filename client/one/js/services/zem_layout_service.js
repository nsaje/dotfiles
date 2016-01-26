/* globals JSON */
"use strict";

oneApp.factory('zemLayoutService', ['$location', function ($location) {
    // Because filteredSources is being watched (through getFilteredSources function) from
    // different controllers, it has to always point to the same array. Special care is taken
    // to never replace the reference (no assignments to this variable) so the array is
    // always modified in place.
    var showNavigationPane = [];
    var showGraph = false;
    var showInfobox = false;

    function toggleNavigationPaneVisible () {
        showNavigationPane = !showNavigationPane;
    }

    function isNavigationPaneVisible () {
        return showNavigationPane;
    }

    function toggleGraphVisible () {
        showGraph = !showGraph;
    }

    function isGraphVisible () {
        return showGraph;
    }

    function toggleInfoboxVisible () {
        showInfobox = !showInfobox;
    }

    function isInfoboxVisible () {
        return showInfobox;
    }

    return {
        toggleNavigationPaneVisible: toggleNavigationPaneVisible,
        isNavigationPaneVisible: isNavigationPaneVisible,
        toggleGraphVisible: toggleGraphVisible,
        isGraphVisible: isGraphVisible,
        toggleInfoboxVisible: toggleInfoboxVisible,
        isInfoboxVisible: isInfoboxVisible
    };
}]);
