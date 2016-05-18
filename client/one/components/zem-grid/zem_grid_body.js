/* globals oneApp */
'use strict';

oneApp.directive('zemGridBody', ['$timeout', 'zemGridConstants', 'zemGridUIService', function ($timeout, zemGridConstants, zemGridUIService) {

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
            pubsub: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_body.html',
        link: function (scope, element) {
            scope.ctrl.grid.body.element = element;
            scope.state = {
                renderedRows: [],
            };

            var visibleRows;
            var pubsub = scope.ctrl.pubsub;
            var requestAnimFrame = (function () {
                return window.requestAnimationFrame       ||
                       window.webkitRequestAnimationFrame ||
                       window.mozRequestAnimationFrame    ||
                       window.oRequestAnimationFrame      ||
                       window.msRequestAnimationFrame     ||
                       function (callback) {
                           window.setTimeout(callback, 1000 / 60);
                       };
            })();

            function getTranslateYStyle (top) {
                var translateCssProperty = 'translateY(' + top + 'px)';

                return {
                    '-webkit-transform': translateCssProperty,
                    '-ms-transform': translateCssProperty,
                    'transform': translateCssProperty,
                    'display': 'block',
                };
            }

            var updateInProgress = false;
            function requestUpdate (cb) {
                if (!updateInProgress) {
                    requestAnimFrame(cb);
                    updateInProgress = true;
                }
            }

            var prevScrollLeft = 0;
            var prevScrollTop = 0;
            function scrollListener (event) {
                if (prevScrollLeft !== event.target.scrollLeft) {
                    prevScrollLeft = event.target.scrollLeft;
                    pubsub.notify(
                        pubsub.EVENTS.BODY_HORIZONTAL_SCROLL,
                        prevScrollLeft
                    );
                }

                if (prevScrollTop !== event.target.scrollTop) {
                    prevScrollTop = event.target.scrollTop;
                    pubsub.notify(
                        pubsub.EVENTS.BODY_VERTICAL_SCROLL,
                        prevScrollTop
                    );
                }
            }

            var prevFirstRow = 0;
            function handleVerticalScroll (scrollTop) {
                var currFirstRow = Math.max(
                    Math.floor(scrollTop / zemGridConstants.gridBodyRendering.ROW_HEIGHT),
                    0
                );

                var delta = currFirstRow - prevFirstRow;
                if (Math.abs(delta) >= zemGridConstants.gridBodyRendering.NUM_OF_ROWS_PER_PAGE + zemGridConstants.gridBodyRendering.NUM_OF_PRERENDERED_ROWS) {
                    // Rows can't be reused, reinitialize visible rows
                    initRenderedRows(currFirstRow, true);
                } else if (delta) {
                    // Some rows can be reused, update visible rows
                    updateRenderedRows(currFirstRow, delta, true);
                }
            }

            function updateRenderedRows (firstRow, delta, digest) {
                requestUpdate(function () {
                    var lastRow, i, row;
                    var renderedRows = [];
                    var availableIndexes = [];

                    if (delta > 0) {
                        // Add new rows to the bottom and reuse indexes from the top
                        scope.state.renderedRows.slice(0, delta).forEach(function (row) {
                            availableIndexes.push(row.index);
                        });
                        renderedRows = scope.state.renderedRows.slice(delta);
                        if (visibleRows.length <= firstRow + zemGridConstants.gridBodyRendering.NUM_OF_ROWS_PER_PAGE + zemGridConstants.gridBodyRendering.NUM_OF_PRERENDERED_ROWS) {
                            lastRow = zemGridConstants.gridBodyRendering.NUM_OF_ROWS_PER_PAGE + zemGridConstants.gridBodyRendering.NUM_OF_PRERENDERED_ROWS;
                        } else {
                            lastRow = firstRow + zemGridConstants.gridBodyRendering.NUM_OF_ROWS_PER_PAGE + zemGridConstants.gridBodyRendering.NUM_OF_PRERENDERED_ROWS;
                        }
                        for (i = lastRow - delta; i < lastRow; i++) {
                            row = visibleRows[i];
                            if (!row.isDummy) {
                                row.style = getTranslateYStyle(i * zemGridConstants.gridBodyRendering.ROW_HEIGHT);
                            }
                            row.index = availableIndexes.shift();
                            renderedRows.push(row);
                        }
                    } else {
                        // Add new rows to the top and reuse indexes from the bottom
                        scope.state.renderedRows.slice(delta).forEach(function (row) {
                            availableIndexes.push(row.index);
                        });
                        renderedRows = scope.state.renderedRows.slice(0, delta);
                        if (visibleRows.length <= firstRow + zemGridConstants.gridBodyRendering.NUM_OF_ROWS_PER_PAGE + zemGridConstants.gridBodyRendering.NUM_OF_PRERENDERED_ROWS) {
                            lastRow = Math.abs(delta) - 1;
                        } else {
                            lastRow = firstRow + Math.abs(delta) - 1;
                        }
                        for (i = lastRow; i >= firstRow; i--) {
                            row = visibleRows[i];
                            if (!row.isDummy) {
                                row.style = getTranslateYStyle(i * zemGridConstants.gridBodyRendering.ROW_HEIGHT);
                            }
                            row.index = availableIndexes.shift();
                            renderedRows.unshift(row);
                        }
                    }

                    scope.state.renderedRows = renderedRows;
                    if (digest) {
                        scope.$digest();
                    }

                    prevFirstRow = firstRow;
                    updateInProgress = false;
                });
            }

            function initRenderedRows (firstRow, digest) {
                requestUpdate(function () {
                    var row;
                    var renderedRows = [];
                    var index = 0;
                    var lastRow;
                    if (visibleRows.length <= firstRow + zemGridConstants.gridBodyRendering.NUM_OF_ROWS_PER_PAGE + zemGridConstants.gridBodyRendering.NUM_OF_PRERENDERED_ROWS) {
                        lastRow = zemGridConstants.gridBodyRendering.NUM_OF_ROWS_PER_PAGE + zemGridConstants.gridBodyRendering.NUM_OF_PRERENDERED_ROWS;
                    } else {
                        lastRow = firstRow + zemGridConstants.gridBodyRendering.NUM_OF_ROWS_PER_PAGE + zemGridConstants.gridBodyRendering.NUM_OF_PRERENDERED_ROWS;
                    }

                    for (var i = firstRow; i < lastRow; i++) {
                        row = visibleRows[i];
                        if (!row.isDummy) {
                            row.style = getTranslateYStyle(i * zemGridConstants.gridBodyRendering.ROW_HEIGHT);
                        }
                        row.index = index++;
                        renderedRows.push(row);
                    }

                    scope.state.renderedRows = renderedRows;
                    if (digest) {
                        scope.$digest();
                    }

                    prevFirstRow = firstRow;
                    updateInProgress = false;
                });
            }

            var visibleRowsCount;
            function updateVisibleRows () {
                visibleRows = [];
                visibleRowsCount = 0;
                scope.ctrl.grid.body.rows.forEach(function (row) {
                    if (row.visible) {
                        visibleRows.push(row);
                        visibleRowsCount++;
                    }
                });

                var dummyRow = Object.create(visibleRows[0]);
                dummyRow.isDummy = true;
                dummyRow.style = {'display': 'none'};

                // Always have at least 'NUM_OF_ROWS_PER_PAGE' rows in visibleRows
                while (visibleRows.length < zemGridConstants.gridBodyRendering.NUM_OF_ROWS_PER_PAGE) {
                    visibleRows.push(Object.create(dummyRow));
                }
                // Append additional hidden dummy rows so that 'NUM_OF_ROWS_PER_PAGE' + 'NUM_OF_PRERENDERED_ROWS' DOM
                // elements are always rendered
                for (var i = 0; i < zemGridConstants.gridBodyRendering.NUM_OF_PRERENDERED_ROWS; i++) {
                    visibleRows.push(Object.create(dummyRow));
                }
            }

            function getTableHeightStyle () {
                var height = visibleRowsCount * zemGridConstants.gridBodyRendering.ROW_HEIGHT;
                return {
                    height: height + 'px',
                };
            }

            pubsub.register(pubsub.EVENTS.BODY_VERTICAL_SCROLL, function (event, scrollTop) {
                handleVerticalScroll(scrollTop);
            });

            pubsub.register(pubsub.EVENTS.ROWS_UPDATED, function () {
                updateVisibleRows();
                scope.fullTableHeight = getTableHeightStyle();
                initRenderedRows(prevFirstRow, true);

                // $timeout(function () {
                //     scope.ctrl.grid.ui.state.bodyRendered = true;
                //     scope.ctrl.grid.body.element = element;
                //     zemGridUIService.resizeGridColumns(scope.ctrl.grid);
                // }, 0, false);
            });

            scope.$watch('ctrl.grid.body.rows', function (rows) {
                if (rows) {
                    updateVisibleRows();
                    scope.fullTableHeight = getTableHeightStyle();
                    initRenderedRows(0, true);

                    $timeout(function () {
                        scope.ctrl.grid.ui.state.bodyRendered = true;
                        scope.ctrl.grid.body.element = element;
                        zemGridUIService.resizeGridColumns(scope.ctrl.grid);
                    }, 0, false);
                }
            });

            element.on('scroll', scrollListener);
        },
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
