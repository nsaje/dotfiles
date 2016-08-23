/* globals oneApp */
'use strict';

// TODO:
// - refactor grid object

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
            var grid = scope.ctrl.grid;
            var pubsub = grid.meta.pubsub;

            grid.body.ui.element = element;
            grid.body.ui.scrollLeft = 0;
            grid.body.ui.scrollTop = 0;
            scope.state = {
                renderedRows: [],
            };

            var visibleRows;
            var numberOfRenderedRows = zemGridConstants.gridBodyRendering.NUM_OF_ROWS_PER_PAGE
                                     + zemGridConstants.gridBodyRendering.NUM_OF_PRERENDERED_ROWS;

            function scrollListener (event) {
                if (grid.body.ui.scrollLeft !== event.target.scrollLeft) {
                    grid.body.ui.scrollLeft = event.target.scrollLeft;
                    pubsub.notify(
                        pubsub.EVENTS.BODY_HORIZONTAL_SCROLL,
                        grid.body.ui.scrollLeft
                    );
                }

                if (grid.body.ui.scrollTop !== event.target.scrollTop) {
                    grid.body.ui.scrollTop = event.target.scrollTop;
                    pubsub.notify(
                        pubsub.EVENTS.BODY_VERTICAL_SCROLL,
                        grid.body.ui.scrollTop
                    );
                }
            }

            var visibleRowsCount;
            function updateVisibleRows () {
                visibleRows = [];
                visibleRowsCount = 0;
                grid.body.rows.forEach(function (row) {
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

                scope.ctrl.grid.body.visibleRows = visibleRows;
                scope.state.renderedRows = visibleRows.slice(0, numberOfRenderedRows);
            }

            function getTranslateYStyle (top) {
                var translateCssProperty = 'translateY(' + top + 'px)';

                return {
                    '-webkit-transform': translateCssProperty,
                    '-ms-transform': translateCssProperty,
                    '-moz-transform': translateCssProperty,
                    'transform': translateCssProperty,
                    'display': 'block',
                };
            }

            function updateTableStyle () {
                // Update virtual scroll viewport (zem-gird-table)
                var height = visibleRowsCount * zemGridConstants.gridBodyRendering.ROW_HEIGHT;
                element.find('.zem-grid-table').css({
                    height: height + 'px',
                });

                // Update scroll top position to fit new viewport size
                if (element.height() + element.scrollTop() > height) {
                    var scrollTop = Math.max(0, height - element.height());
                    element.scrollTop(scrollTop);
                    grid.body.ui.scrollTop = scrollTop;
                }
            }

            function updateBody () {
                updateVisibleRows();
                updateTableStyle();
                pubsub.notify(pubsub.EVENTS.BODY_ROWS_UPDATED);
            }

            pubsub.register(pubsub.EVENTS.DATA_UPDATED, updateBody);

            element.on('scroll', scrollListener);
        },
        controller: [function () {}],
    };
}]);
