/* globals oneApp */
'use strict';

// TODO:
// - refactor grid object
// - clean-up and handle empty body.rows array when updating visibleRows array

oneApp.directive('zemGridBody', ['$timeout', 'zemGridConstants', 'zemGridUIService', function ($timeout, zemGridConstants, zemGridUIService) { // eslint-disable-line max-len

    return {
        restrict: 'E',
        replace: true,
        scope: {},
        controllerAs: 'ctrl',
        bindToController: {
            grid: '=',
        },
        templateUrl: '/components/zem-grid/templates/zem_grid_body.html',
        link: function (scope, element) {
            scope.ctrl.grid.body.element = element;
            scope.state = {
                renderedRows: [],
            };

            var visibleRows;
            var numberOfRenderedRows = zemGridConstants.gridBodyRendering.NUM_OF_ROWS_PER_PAGE
                                     + zemGridConstants.gridBodyRendering.NUM_OF_PRERENDERED_ROWS;
            var pubsub = scope.ctrl.grid.meta.pubsub;
            var requestAnimationFrame = zemGridUIService.requestAnimationFrame;

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
                    requestAnimationFrame(cb);
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

                updateRenderedRows(currFirstRow, true);
            }

            function updateRenderedRows (firstRow, digest) {
                requestUpdate(function () {
                    scope.state.renderedRows = visibleRows.slice(firstRow, firstRow + numberOfRenderedRows);
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
                        row.style = getTranslateYStyle(
                            visibleRowsCount * zemGridConstants.gridBodyRendering.ROW_HEIGHT
                        );
                        visibleRows.push(row);
                        visibleRowsCount++;
                    }
                });

                if (visibleRowsCount > zemGridConstants.gridBodyRendering.NUM_OF_ROWS_PER_PAGE) {
                    var dummyRow;
                    for (var j = 0; j < zemGridConstants.gridBodyRendering.NUM_OF_PRERENDERED_ROWS; j++) {
                        dummyRow = Object.create(visibleRows[0]);
                        dummyRow.style = {'display': 'none'};
                        visibleRows.push(dummyRow);
                    }
                }

                for (var i = 0; i < visibleRows.length; i++) {
                    visibleRows[i].index = i % numberOfRenderedRows;
                }
            }

            function getTableHeightStyle () {
                var height = visibleRowsCount * zemGridConstants.gridBodyRendering.ROW_HEIGHT;
                return {
                    height: height + 'px',
                };
            }

            function updateBody () {
                updateVisibleRows();
                scope.fullTableHeight = getTableHeightStyle();

                if (visibleRowsCount < (prevFirstRow + numberOfRenderedRows)) {
                    prevFirstRow = Math.max((visibleRowsCount - numberOfRenderedRows), 0);
                }

                updateRenderedRows(prevFirstRow, true);

                $timeout(function () {
                    scope.ctrl.grid.ui.state.bodyRendered = true;
                    scope.ctrl.grid.body.element = element;
                    zemGridUIService.resizeGridColumns(scope.ctrl.grid);
                }, 0, false);
            }

            pubsub.register(pubsub.EVENTS.METADATA_UPDATED, function () {
                prevFirstRow = 0;
            });

            pubsub.register(pubsub.EVENTS.DATA_UPDATED, updateBody);

            pubsub.register(pubsub.EVENTS.BODY_VERTICAL_SCROLL, function (event, scrollTop) {
                handleVerticalScroll(scrollTop);
            });

            element.on('scroll', scrollListener);
        },
        controller: [function () {}],
    };
}]);
