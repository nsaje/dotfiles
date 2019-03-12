angular
    .module('one.services')
    .service('zemSelectionService', function(
        $rootScope,
        $location,
        zemPubSubService
    ) {
        this.init = init;
        this.getSelection = getSelection;
        this.isIdInSelected = isIdInSelected;
        this.isIdInUnselected = isIdInUnselected;
        this.isTotalsSelected = isTotalsSelected;
        this.isAllSelected = isAllSelected;
        this.getSelectedBatch = getSelectedBatch;
        this.setSelection = setSelection;
        this.remove = remove;
        this.selectTotals = selectTotals;
        this.unselectTotals = unselectTotals;
        this.selectAll = selectAll;
        this.unselectAll = unselectAll;

        this.onSelectionUpdate = onSelectionUpdate;

        var pubSub = zemPubSubService.createInstance();
        var EVENTS = {
            ON_SELECTION_UPDATE: 'zem-selection-on-selection-update',
        };

        var SELECTED = 'selected';
        var UNSELECTED = 'unselected';
        var TOTALS_UNSELECTED = 'totalsUnselected';
        var ALL = 'all';
        var BATCH = 'batch';

        var URL_PARAMS_TYPES = {
            boolean: 'boolean',
            number: 'number',
            list: 'list',
        };

        var URL_PARAMS = {};
        URL_PARAMS[SELECTED] = {
            name: 'selected_ids',
            type: URL_PARAMS_TYPES.list,
        };
        URL_PARAMS[UNSELECTED] = {
            name: 'unselected_ids',
            type: URL_PARAMS_TYPES.list,
        };
        URL_PARAMS[TOTALS_UNSELECTED] = {
            name: 'totals_unselected',
            type: URL_PARAMS_TYPES.boolean,
        };
        URL_PARAMS[ALL] = {
            name: 'selected_all',
            type: URL_PARAMS_TYPES.boolean,
        };
        URL_PARAMS[BATCH] = {
            name: 'selected_batch_id',
            type: URL_PARAMS_TYPES.number,
        };

        var selection;

        init();

        //
        // Public methods
        //
        function init() {
            selection = initFromUrlParams();

            $rootScope.$on('$zemStateChangeStart', function() {
                clear();
                pubSub.notify(EVENTS.ON_SELECTION_UPDATE, getSelection());
            });
        }

        function getSelection() {
            return angular.copy(selection);
        }

        function isIdInSelected(id) {
            return (
                id &&
                isSelectedSet() &&
                selection[SELECTED].indexOf(id.toString()) !== -1
            );
        }

        function isIdInUnselected(id) {
            return (
                id &&
                isUnselectedSet() &&
                selection[UNSELECTED].indexOf(id.toString()) !== -1
            );
        }

        function isTotalsSelected() {
            return !selection[TOTALS_UNSELECTED];
        }

        function isAllSelected() {
            return selection[ALL];
        }

        function getSelectedBatch() {
            return selection[BATCH];
        }

        function setSelection(newSelection) {
            var newSelectionCopy = angular.copy(newSelection);
            newSelectionCopy[SELECTED] = convertIdsToArray(
                newSelectionCopy[SELECTED]
            );
            newSelectionCopy[UNSELECTED] = convertIdsToArray(
                newSelectionCopy[UNSELECTED]
            );
            newSelectionCopy = angular.extend(
                {},
                getDefaultSelection(),
                newSelectionCopy
            );
            if (!angular.equals(selection, newSelectionCopy)) {
                selection = newSelectionCopy;
                setUrlParams(selection);
                pubSub.notify(EVENTS.ON_SELECTION_UPDATE, getSelection());
            }
        }

        function remove(ids) {
            removeFromSelected(ids);
            if (isAllSelected() || selection[BATCH]) {
                addToUnselected(ids);
            }
        }

        function selectTotals() {
            selection[TOTALS_UNSELECTED] = false;
            setUrlParams(selection);
            pubSub.notify(EVENTS.ON_SELECTION_UPDATE, getSelection());
        }

        function unselectTotals() {
            selection[TOTALS_UNSELECTED] = true;
            setUrlParams(selection);
            pubSub.notify(EVENTS.ON_SELECTION_UPDATE, getSelection());
        }

        function selectAll() {
            clear();
            selection[ALL] = true;
            selection[TOTALS_UNSELECTED] = false;
            setUrlParams(selection);
            pubSub.notify(EVENTS.ON_SELECTION_UPDATE, getSelection());
        }

        function unselectAll() {
            clear();
            pubSub.notify(EVENTS.ON_SELECTION_UPDATE, getSelection());
        }

        //
        // Events
        //
        function onSelectionUpdate(callback) {
            return pubSub.register(EVENTS.ON_SELECTION_UPDATE, callback);
        }

        //
        // Private methods
        //
        function clear() {
            selection = getDefaultSelection();
            setUrlParams(selection);
        }

        function isSelectedSet() {
            return selection[SELECTED].length > 0;
        }

        function isUnselectedSet() {
            return selection[UNSELECTED].length > 0;
        }

        function removeFromSelected(ids) {
            ids = convertIdsToArray(ids);

            var updated = false;
            ids.forEach(function(id) {
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

        function addToUnselected(ids) {
            ids = convertIdsToArray(ids);

            var updated = false;
            ids.forEach(function(id) {
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

        function initFromUrlParams() {
            var params = $location.search();
            var selection = getDefaultSelection();

            angular.forEach(URL_PARAMS, function(param, key) {
                var value = params[param.name];

                if (value && param.type === URL_PARAMS_TYPES.list) {
                    value = value
                        .split(',')
                        .filter(function(item) {
                            return (
                                item !== null &&
                                item !== undefined &&
                                item.toString() !== ''
                            );
                        })
                        .map(function(item) {
                            return item.toString();
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

        function setUrlParams(selection) {
            angular.forEach(selection, function(value, key) {
                if (!value || (value instanceof Array && value.length === 0)) {
                    value = null;
                } else if (value instanceof Array) {
                    value = value.join(',');
                }
                $location.search(URL_PARAMS[key].name, value).replace();
            });
        }

        function getDefaultSelection() {
            var emptySelection = {};
            emptySelection[SELECTED] = [];
            emptySelection[UNSELECTED] = [];
            emptySelection[TOTALS_UNSELECTED] = false;
            emptySelection[ALL] = false;
            emptySelection[BATCH] = null;
            return emptySelection;
        }

        function convertIdsToArray(ids) {
            if (ids instanceof Array) {
                return ids.map(function(id) {
                    return id.toString();
                });
            }

            if (ids) {
                return [ids.toString()];
            }

            return [];
        }
    });
