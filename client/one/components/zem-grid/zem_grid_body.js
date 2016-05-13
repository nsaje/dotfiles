/* globals oneApp */
'use strict';

oneApp.directive('zemGridBody', ['$timeout', 'zemGridConstants', function ($timeout, zemGridConstants) {

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
            var visibleRows;
            scope.state = {
                renderedRows: [],
            };

            // TODO: fill 'load more' rows with fake data

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

                if (Math.abs(delta) >= zemGridConstants.gridBodyRendering.NUM_OF_RENDERED_ROWS ||
                    scope.state.renderedRows.length < zemGridConstants.gridBodyRendering.NUM_OF_RENDERED_ROWS) {
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
                        lastRow = firstRow + zemGridConstants.gridBodyRendering.NUM_OF_RENDERED_ROWS;
                        for (i = lastRow - delta; i < lastRow; i++) {
                            row = visibleRows[i];
                            if (row) {
                                row.index = availableIndexes.shift();
                                row.style = getTranslateYStyle(i * zemGridConstants.gridBodyRendering.ROW_HEIGHT);
                                renderedRows.push(row);
                            }
                        }
                    } else {
                        // Add new rows to the top and reuse indexes from the bottom
                        scope.state.renderedRows.slice(delta).forEach(function (row) {
                            availableIndexes.push(row.index);
                        });
                        renderedRows = scope.state.renderedRows.slice(0, delta);
                        lastRow = firstRow + Math.abs(delta) - 1;
                        for (i = lastRow; i >= firstRow; i--) {
                            row = visibleRows[i];
                            if (row) {
                                row.index = availableIndexes.shift();
                                row.style = getTranslateYStyle(i * zemGridConstants.gridBodyRendering.ROW_HEIGHT);
                                renderedRows.unshift(row);
                            }
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
                    var lastRow = firstRow + zemGridConstants.gridBodyRendering.NUM_OF_RENDERED_ROWS;
                    for (var i = firstRow; i < lastRow; i++) {
                        row = visibleRows[i];
                        if (row) {
                            row.index = index++;
                            row.style = getTranslateYStyle(i * zemGridConstants.gridBodyRendering.ROW_HEIGHT);
                            renderedRows.push(row);
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

            function updateVisibleRows () {
                visibleRows = [];
                scope.ctrl.grid.body.rows.forEach(function (row) {
                    if (row.visible) {
                        visibleRows.push(row);
                    }
                });
            }

            pubsub.register(pubsub.EVENTS.BODY_VERTICAL_SCROLL, function (event, scrollTop) {
                handleVerticalScroll(scrollTop);
            });

            pubsub.register(pubsub.EVENTS.ROWS_UPDATED, function () {
                updateVisibleRows();
                scope.fullTableHeight = {
                    height: (visibleRows.length * zemGridConstants.gridBodyRendering.ROW_HEIGHT) + 'px',
                };
                initRenderedRows(prevFirstRow, true);
            });

            scope.$watch('ctrl.grid.body.rows', function (rows) {
                if (rows) {
                    updateVisibleRows();
                    scope.fullTableHeight = {
                        height: (visibleRows.length * zemGridConstants.gridBodyRendering.ROW_HEIGHT) + 'px',
                    };
                    initRenderedRows(0, true);

                    $timeout(function () {
                        // Calculate columns widths after body rows are rendered
                        var columns = element.querySelectorAll('.zem-grid-cell');
                        columns.each(function (index, column) {
                            var columnWidth = column.offsetWidth;
                            if (scope.ctrl.grid.ui.columnWidths[index] < columnWidth) {
                                scope.ctrl.grid.ui.columnWidths[index] = columnWidth;
                            }
                        });
                    }, 0, false);
                }
            });

            element.on('scroll', scrollListener);
        },
        controller: ['$scope', function ($scope) {
        }],
    };
}]);
