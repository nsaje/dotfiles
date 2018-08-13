angular.module('one.common').factory('zemSelectDataStore', function() {
    function UISelectDataStore(initialPromise) {
        //
        // Data store for zemSelect. It provides a very simple interface with a
        // single function - search, that returns a promise of results. Constructor
        // inputs and additional parameters to items are data store specific.

        //
        // Public API (interface)
        //
        this.search = search;

        function search(searchQuery) {
            // This implementation of the search function expects items to have
            // the `searchableName` parameter.
            if (searchQuery) {
                return initialPromise.then(function(items) {
                    return simpleSearch(searchQuery, items);
                });
            }

            return initialPromise.then(function(items) {
                return items;
            });
        }

        function simpleSearch(searchQuery, items) {
            searchQuery = searchQuery.toLowerCase();
            return items.filter(function(item) {
                return (
                    item.searchableName.toLowerCase().indexOf(searchQuery) >= 0
                );
            });
        }
    }

    return {
        createInstance: function(initialPromise, getSearchableExpFn) {
            return new UISelectDataStore(initialPromise, getSearchableExpFn);
        },
    };
});
