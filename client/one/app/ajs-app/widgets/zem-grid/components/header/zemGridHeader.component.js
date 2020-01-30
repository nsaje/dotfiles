var ResizeObserverHelper = require('../../../../../shared/helpers/resize-observer.helper')
    .ResizeObserverHelper;
var commonHelpers = require('../../../../../shared/helpers/common.helpers');

angular
    .module('one.widgets')
    .directive('zemGridHeader', function($timeout, zemGridUIService, NgZone) {
        return {
            restrict: 'E',
            replace: true,
            scope: {},
            controllerAs: 'ctrl',
            bindToController: {
                grid: '=',
            },
            template: require('./zemGridHeader.component.html'),
            link: function(scope, element, attributes, ctrl) {
                var pubsub = ctrl.grid.meta.pubsub;
                var requestAnimationFrame =
                    zemGridUIService.requestAnimationFrame;
                ctrl.grid.header.ui.element = element;

                initialize();

                function initialize() {
                    resizeColumns();

                    pubsub.register(
                        pubsub.EVENTS.DATA_UPDATED,
                        scope,
                        resizeColumns
                    );
                    pubsub.register(
                        pubsub.EVENTS.EXT_COLUMNS_UPDATED,
                        scope,
                        resizeColumns
                    );
                    pubsub.register(
                        pubsub.EVENTS.BODY_HORIZONTAL_SCROLL,
                        scope,
                        handleHorizontalScroll
                    );
                    pubsub.register(
                        pubsub.EVENTS.BODY_HORIZONTAL_SCROLL,
                        scope,
                        handleHorizontalScrollPivotColumns
                    );

                    var sidebarContainerContentElement = document.getElementById(
                        'zem-sidebar-container__content'
                    );

                    var resizeObserverHelper = new ResizeObserverHelper(
                        function() {
                            resizeColumns();
                        }
                    );

                    NgZone.runOutsideAngular(function() {
                        if (
                            commonHelpers.isDefined(
                                sidebarContainerContentElement
                            )
                        ) {
                            resizeObserverHelper.observe(
                                sidebarContainerContentElement
                            );
                            sidebarContainerContentElement.addEventListener(
                                'scroll',
                                updateStickyElements
                            );
                        }
                    });
                    scope.$on('$destroy', function() {
                        if (
                            commonHelpers.isDefined(
                                sidebarContainerContentElement
                            )
                        ) {
                            resizeObserverHelper.unobserve(
                                sidebarContainerContentElement
                            );
                            sidebarContainerContentElement.removeEventListener(
                                'scroll',
                                updateStickyElements
                            );
                        }
                    });
                }

                function updateStickyElements() {
                    NgZone.runOutsideAngular(function() {
                        zemGridUIService.updateStickyElements(ctrl.grid);
                    });
                }

                function resizeColumns() {
                    NgZone.runOutsideAngular(function() {
                        // Workaround: call resize 2 times - in some cases  (e.g. initialization) table is not
                        // yet rendered causing resize to function on empty table. On the other hand call resize
                        // immediately to prevent flickering if table is already rendered (e.g. toggling columns)
                        zemGridUIService.resizeGridColumns(ctrl.grid);
                        updateStickyElements();
                        $timeout(
                            function() {
                                requestAnimationFrame(function() {
                                    zemGridUIService.resizeGridColumns(
                                        ctrl.grid
                                    );
                                    updateStickyElements();
                                });
                            },
                            0,
                            false
                        );
                    });
                }

                function handleHorizontalScroll() {
                    NgZone.runOutsideAngular(function() {
                        var leftOffset = -1 * ctrl.grid.body.ui.scrollLeft;
                        var translateCssProperty =
                            'translateX(' + leftOffset + 'px)';

                        element.find('.zem-grid-header').css({
                            '-webkit-transform': translateCssProperty,
                            '-moz-transform': translateCssProperty,
                            '-ms-transform': translateCssProperty,
                            transform: translateCssProperty,
                        });
                    });
                }

                var scrolling = false;

                var scrollStarted = function() {
                    NgZone.runOutsideAngular(function() {
                        // On start scroll move pivot columns to original position
                        scrolling = true;
                        zemGridUIService.updatePivotColumns(ctrl.grid, 0);
                    });
                };

                var scrollStopped = debounce(function() {
                    NgZone.runOutsideAngular(function() {
                        // Animate fade-in
                        // First set position to be hidden on the left side and after that
                        // slide-in columns to correct fixed position
                        var startPosition = Math.max(
                            0,
                            ctrl.grid.body.ui.scrollLeft -
                                ctrl.grid.ui.pivotColumnsWidth
                        );
                        var endPosition = ctrl.grid.body.ui.scrollLeft;
                        zemGridUIService.updatePivotColumns(
                            ctrl.grid,
                            startPosition
                        );
                        $timeout(function() {
                            zemGridUIService.updatePivotColumns(
                                ctrl.grid,
                                endPosition,
                                true
                            );
                            scrolling = false;
                        });
                    });
                }, 100);

                function handleHorizontalScrollPivotColumns() {
                    NgZone.runOutsideAngular(function() {
                        // WORKAROUND: pivot columns are not synced with scroll on hiDPI screens (retina, mobile)
                        // In case of HiDPI, pivot column are animated. FIXME: find proper solution for this problem
                        if (window.devicePixelRatio > 1) {
                            // Animate on HiDPI devices - scroll is not in sync with pivot columns translate
                            if (!scrolling) {
                                scrollStarted();
                            } else {
                                scrollStopped();
                            }
                        } else {
                            zemGridUIService.updatePivotColumns(
                                ctrl.grid,
                                ctrl.grid.body.ui.scrollLeft
                            );
                        }
                    });
                }

                // TODO: create util service and move this function there
                function debounce(func, wait, immediate) {
                    var timeout;
                    return function() {
                        var context = this,
                            args = arguments;
                        var later = function() {
                            timeout = null;
                            if (!immediate) func.apply(context, args);
                        };
                        var callNow = immediate && !timeout;
                        clearTimeout(timeout);
                        timeout = setTimeout(later, wait);
                        if (callNow) func.apply(context, args);
                    };
                }
            },
            controller: function($scope) {
                var vm = this;
                var pubsub = this.grid.meta.pubsub;
                var columnsService = this.grid.meta.columnsService;

                vm.model = {};

                initialize();

                function initialize() {
                    initializeColumns();
                    pubsub.register(
                        pubsub.EVENTS.EXT_COLUMNS_UPDATED,
                        $scope,
                        initializeColumns
                    );
                }

                function initializeColumns() {
                    vm.model.visibleColumns = columnsService.getVisibleColumns();

                    // visibleColumns is shared with body to optimize virtual scroll performance
                    vm.grid.header.visibleColumns = vm.model.visibleColumns;

                    // [UI/UX] Resize columns before first render (avoid jumps)
                    $timeout(function() {
                        zemGridUIService.resizeGridColumns(vm.grid);
                        vm.visible = true;
                    });
                }
            },
        };
    });
