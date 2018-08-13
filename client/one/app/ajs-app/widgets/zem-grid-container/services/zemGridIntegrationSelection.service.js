angular
    .module('one.widgets')
    .service('zemGridIntegrationSelectionService', function(
        zemSelectionService,
        zemGridConstants,
        zemGridEndpointColumns
    ) {
        // eslint-disable-line
        this.createGridSelection = createGridSelection;
        this.createCoreSelection = createCoreSelection;

        //
        // Public methods
        //
        function createGridSelection(gridApi) {
            var gridSelection = gridApi.getSelection();
            var rows = gridApi.getRows();

            setGridSelectionFilter(gridApi);

            gridSelection = setGridSelectedAndUnselectedRows(
                gridSelection,
                rows
            );
            gridSelection = addFooterRowToGridSelection(
                gridApi,
                gridSelection,
                rows
            );

            return gridSelection;
        }

        function createCoreSelection(gridApi) {
            var gridSelection = gridApi.getSelection();
            var selection = {
                selected: [],
                unselected: [],
                totalsUnselected: false,
            };

            switch (gridSelection.type) {
                case zemGridConstants.gridSelectionFilterType.ALL:
                    selection.all = true;
                    break;
                case zemGridConstants.gridSelectionFilterType.CUSTOM:
                    selection.batch = gridSelection.filter.batch.id;
                    selection.totalsUnselected = true;
                    break;
                case zemGridConstants.gridSelectionFilterType.NONE:
                    selection.totalsUnselected = true;
                    break;
            }

            gridSelection.selected.forEach(function(row) {
                if (row.level === zemGridConstants.gridRowLevel.FOOTER) {
                    selection.totalsUnselected = false;
                } else if (row.level === zemGridConstants.gridRowLevel.BASE) {
                    var id = parseInt(row.data.breakdownId);
                    if (!isNaN(id)) {
                        selection.selected.push(id);
                    }
                }
            });

            gridSelection.unselected.forEach(function(row) {
                if (row.level === zemGridConstants.gridRowLevel.FOOTER) {
                    selection.totalsUnselected = true;
                } else if (row.level === zemGridConstants.gridRowLevel.BASE) {
                    var id = parseInt(row.data.breakdownId);
                    if (!isNaN(id)) {
                        selection.unselected.push(id);
                    }
                }
            });

            if (gridApi.isSelectionEmpty()) {
                // Select footer row if no other row is selected in grid
                selection.totalsUnselected = false;
            }

            return selection;
        }

        //
        // Private methods
        //
        function setGridSelectionFilter(gridApi) {
            var metaData = gridApi.getMetaData();
            var selectedBatch = zemSelectionService.getSelectedBatch();

            if (zemSelectionService.isAllSelected()) {
                gridApi.setSelectionFilter(
                    zemGridConstants.gridSelectionFilterType.ALL
                );
            } else if (
                selectedBatch &&
                metaData &&
                metaData.ext &&
                metaData.ext.batches
            ) {
                var batchSelectionFilter = getBatchSelectionFilter(
                    selectedBatch,
                    metaData.ext.batches
                );
                if (batchSelectionFilter) {
                    gridApi.setSelectionFilter(
                        zemGridConstants.gridSelectionFilterType.CUSTOM,
                        batchSelectionFilter
                    );
                }
            } else {
                gridApi.setSelectionFilter(
                    zemGridConstants.gridSelectionFilterType.NONE
                );
            }
        }

        function getBatchSelectionFilter(selectedBatch, batches) {
            for (var i = 0; i < batches.length; i++) {
                var batch = batches[i];
                if (parseInt(batch.id) === selectedBatch) {
                    return {
                        name: batch.name,
                        batch: batch,
                        callback: function(row) {
                            return (
                                row.data.stats[
                                    zemGridEndpointColumns.COLUMNS.batchId.field
                                ].value === batch.id
                            );
                        },
                    };
                }
            }
        }

        function setGridSelectedAndUnselectedRows(gridSelection, rows) {
            gridSelection.selected = [];
            gridSelection.unselected = [];

            rows.forEach(function(row) {
                if (
                    row.level === zemGridConstants.gridRowLevel.BASE &&
                    zemSelectionService.isIdInSelected(row.data.breakdownId)
                ) {
                    gridSelection.selected.push(row);
                } else if (
                    row.level === zemGridConstants.gridRowLevel.BASE &&
                    zemSelectionService.isIdInUnselected(row.data.breakdownId)
                ) {
                    gridSelection.unselected.push(row);
                }
            });

            return gridSelection;
        }

        function addFooterRowToGridSelection(gridApi, gridSelection, rows) {
            var footerRow = getFooterRowFromGridRows(rows);

            if (
                footerRow &&
                (zemSelectionService.isTotalsSelected() ||
                    gridApi.isSelectionEmpty())
            ) {
                // Select footer row if totals are selected in zemSelectionService or no other row is selected in grid
                gridSelection.selected.push(footerRow);
            } else if (
                footerRow &&
                !zemSelectionService.isTotalsSelected() &&
                (zemSelectionService.isAllSelected() ||
                    zemSelectionService.getSelectedBatch())
            ) {
                // Unselect footer row if all or batch are selected in zemSelectionService and totals are unselected
                gridSelection.unselected.push(footerRow);
            }

            return gridSelection;
        }

        function getFooterRowFromGridRows(rows) {
            var row;
            for (var i = 0; i < rows.length; i++) {
                row = rows[i];
                if (row.level === zemGridConstants.gridRowLevel.FOOTER) {
                    return row;
                }
            }
        }
    });
