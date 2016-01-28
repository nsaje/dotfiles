/* globals JSON */
"use strict";

oneApp.factory('zemLayoutService', ['$location', function ($location) {
    var showNavigationPane = true;
    var showGraph = true;
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
