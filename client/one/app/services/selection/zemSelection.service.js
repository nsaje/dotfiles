angular.module('one.services').service('zemSelectionService', function ($rootScope, $location, zemPubSubService) {
    this.init = init;
    this.getSelection = getSelection;
    this.isSelectedSet = isSelectedSet;
    this.isUnselectedSet = isUnselectedSet;
    this.isIdSelected = isIdSelected;
    this.isIdUnselected = isIdUnselected;
    this.isTotalsSelected = isTotalsSelected;
    this.isAllSelected = isAllSelected;
    this.toggle = toggle;
    this.add = add;
    this.remove = remove;
    this.toggleTotals = toggleTotals;
    this.selectTotals = selectTotals;
    this.unselectTotals = unselectTotals;
    this.toggleAll = toggleAll;
    this.selectAll = selectAll;
    this.unselectAll = unselectAll;
    this.selectBatch = selectBatch;

    this.onSelectionUpdate = onSelectionUpdate;


    var pubSub = zemPubSubService.createInstance();
    var EVENTS = {
        ON_SELECTION_UPDATE: 'zem-selection-on-selection-update',
    };

    var SELECTED = 'selected';
    var UNSELECTED = 'unselected';
    var TOTALS = 'totals';
    var ALL = 'all';
    var BATCH = 'batch';

    var URL_PARAMS_TYPES = {
        boolean: 'boolean',
        number: 'number',
        list: 'list',
    };

    var URL_PARAMS = {};
    URL_PARAMS[SELECTED] = {name: 'selected_ids', type: URL_PARAMS_TYPES.list};
    URL_PARAMS[UNSELECTED] = {name: 'unselected_ids', type: URL_PARAMS_TYPES.list};
    URL_PARAMS[TOTALS] = {name: 'selected_totals', type: URL_PARAMS_TYPES.boolean};
    URL_PARAMS[ALL] = {name: 'selected_all', type: URL_PARAMS_TYPES.boolean};
    URL_PARAMS[BATCH] = {name: 'selected_batch_id', type: URL_PARAMS_TYPES.number};

    var selection;


    init();


    //
    // Public methods
    //
    function init () {
        selection = initFromUrlParams();

        $rootScope.$on('$stateChangeStart', function () {
            clear();
            pubSub.notify(EVENTS.ON_SELECTION_UPDATE, getSelection());
        });
    }

    function getSelection () {
        return angular.copy(selection);
    }

    function isSelectedSet () {
        return selection[SELECTED].length > 0;
    }

    function isUnselectedSet () {
        return selection[UNSELECTED].length > 0;
    }

    function isIdSelected (id) {
        id = parseInt(id);
        return isAllSelected() && !isIdUnselected(id) || isSelectedSet() && selection[SELECTED].indexOf(id) !== -1;
    }

    function isIdUnselected (id) {
        return isUnselectedSet() && selection[UNSELECTED].indexOf(parseInt(id)) !== -1;
    }

    function isTotalsSelected () {
        return selection[TOTALS];
    }

    function isAllSelected () {
        return selection[ALL];
    }

    function toggle (ids) {
        ids = convertIdsToArray(ids);

        var idsToAdd = ids.filter(function (id) {
            return !isIdSelected(id);
        });
        var idsToRemove = ids.filter(function (id) {
            return isIdSelected(id);
        });

        add(idsToAdd);
        remove(idsToRemove);
    }

    function add (ids) {
        ids = convertIdsToArray(ids);

        var updated = false;
        ids.forEach(function (id) {
            if (selection[SELECTED].indexOf(id) === -1) {
                selection[SELECTED].push(id);
                updated = true;
            }
        });

        if (updated) {
            setUrlParams(selection);
            pubSub.notify(EVENTS.ON_SELECTION_UPDATE, getSelection());
        }
    }

    function remove (ids) {
        removeFromSelected(ids);
        if (isAllSelected() || selection[BATCH]) {
            addToUnselected(ids);
        }
    }

    function toggleTotals () {
        if (isTotalsSelected()) {
            unselectTotals();
        } else {
            selectTotals();
        }
    }

    function selectTotals () {
        selection[TOTALS] = true;
        setUrlParams(selection);
        pubSub.notify(EVENTS.ON_SELECTION_UPDATE, getSelection());
    }

    function unselectTotals () {
        selection[TOTALS] = false;
        setUrlParams(selection);
        pubSub.notify(EVENTS.ON_SELECTION_UPDATE, getSelection());
    }

    function toggleAll () {
        if (isAllSelected() && !isUnselectedSet()) {
            unselectAll();
        } else {
            selectAll();
        }
    }

    function selectAll () {
        clear();
        selection[ALL] = true;
        selection[TOTALS] = true;
        setUrlParams(selection);
        pubSub.notify(EVENTS.ON_SELECTION_UPDATE, getSelection());
    }

    function unselectAll () {
        clear();
        pubSub.notify(EVENTS.ON_SELECTION_UPDATE, getSelection());
    }

    function selectBatch (batchId) {
        clear();
        batchId = parseInt(batchId);
        selection[BATCH] = batchId ? batchId : null;
        setUrlParams(selection);
        pubSub.notify(EVENTS.ON_SELECTION_UPDATE, getSelection());
    }


    //
    // Events
    //
    function onSelectionUpdate (callback) {
        return pubSub.register(EVENTS.ON_SELECTION_UPDATE, callback);
    }


    //
    // Private methods
    //
    function clear () {
        selection = getEmptySelection();
        setUrlParams(selection);
    }

    function removeFromSelected (ids) {
        ids = convertIdsToArray(ids);

        var updated = false;
        ids.forEach(function (id) {
            var index = selection[SELECTED].indexOf(id);
            if (index !== -1) {
                selection[SELECTED].splice(index, 1);
                updated = true;
            }
        });

        if (updated) {
            setUrlParams(selection);
            pubSub.notify(EVENTS.ON_SELECTION_UPDATE, getSelection());
        }
    }

    function addToUnselected (ids) {
        ids = convertIdsToArray(ids);

        var updated = false;
        ids.forEach(function (id) {
            if (selection[UNSELECTED].indexOf(id) === -1) {
                selection[UNSELECTED].push(id);
                updated = true;
            }
        });

        if (updated) {
            setUrlParams(selection);
            pubSub.notify(EVENTS.ON_SELECTION_UPDATE, getSelection());
        }
    }

    function initFromUrlParams () {
        var params = $location.search();
        var selection = getEmptySelection();

        angular.forEach(URL_PARAMS, function (param, key) {
            var value = params[param.name];

            if (value && param.type === URL_PARAMS_TYPES.list) {
                value = value.split(',')
                    .map(function (item) {
                        return parseInt(item);
                    })
                    .filter(function (item) {
                        return !isNaN(item);
                    });
            } else if (value && param.type === URL_PARAMS_TYPES.number) {
                value = parseInt(value);
            }

            if (value) {
                selection[key] = value;
            }
        });

        return selection;
    }

    function setUrlParams (selection) {
        angular.forEach(selection, function (value, key) {
            if (!value || value instanceof Array && value.length === 0) {
                value = null;
            } else if (value instanceof Array) {
                value = value.join(',');
            }
            $location.search(URL_PARAMS[key].name, value);
        });
    }

    function getEmptySelection () {
        var emptySelection = {};
        emptySelection[SELECTED] = [];
        emptySelection[UNSELECTED] = [];
        emptySelection[TOTALS] = false;
        emptySelection[ALL] = false;
        emptySelection[BATCH] = null;
        return emptySelection;
    }

    function convertIdsToArray (ids) {
        if (ids instanceof Array) {
            return ids.map(function (id) {
                return parseInt(id);
            });
        }

        ids = parseInt(ids);
        if (ids) {
            return [ids];
        }

        return [];
    }
});
