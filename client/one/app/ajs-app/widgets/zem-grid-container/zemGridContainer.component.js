require('./zemGridContainer.component.less');
var arrayHelpers = require('../../../shared/helpers/array.helpers');

angular.module('one.widgets').component('zemGridContainer', {
    template: require('./zemGridContainer.component.html'),
    bindings: {
        entity: '<',
        breakdown: '<',
        level: '<',
    },
    controller: function(
        $scope,
        $timeout,
        zemGridIntegrationService,
        zemGridContainerTabsService,
        zemLocalStorageService,
        zemBidModifierUpdatesService,
        zemSelectionService
    ) {
        var $ctrl = this;

        var LOCAL_STORAGE_KEY_NAMESPACE = 'zemGridContainer';

        $ctrl.constants = constants;
        $ctrl.onGridInitialized = onGridInitialized;

        $ctrl.$onChanges = function(changes) {
            if (changes.entity) {
                $ctrl.tabs = getInitializedTabs();
            }

            var tab = getTab($ctrl.breakdown);
            activateTab(tab);
        };

        function getInitializedTabs() {
            var tabs = zemGridContainerTabsService.createTabOptions(
                $ctrl.entity
            );

            tabs.forEach(function(tab) {
                if (!arrayHelpers.isEmpty(tab.options)) {
                    var savedBreakdown = zemLocalStorageService.get(
                        tab.localStorageKey,
                        LOCAL_STORAGE_KEY_NAMESPACE
                    );
                    if (savedBreakdown) {
                        var option = tab.options.find(function(option) {
                            return option.breakdown === savedBreakdown;
                        });
                        if (option) {
                            mapFromTo(option, tab);
                        }
                    }
                }
            });

            return angular.copy(tabs);
        }

        function activateTab(tab) {
            selectTab(tab);

            if (isGridTab(tab)) {
                activateGridTab(tab);
            } else {
                tab.activated = true;
            }
        }

        function isGridTab(tab) {
            return tab.breakdown !== constants.breakdown.INSIGHTS;
        }

        function activateGridTab(tab) {
            zemSelectionService.setSelection([]);
            if (!tab.activated) {
                $timeout(function() {
                    var $childScope = $scope.$new();
                    tab.gridIntegrationService = zemGridIntegrationService.createInstance(
                        $childScope
                    );
                    tab.gridIntegrationService.initialize($ctrl.entity);
                    tab.gridIntegrationService.configureDataSource(
                        $ctrl.entity,
                        tab.breakdown
                    );
                    tab.grid = tab.gridIntegrationService.getGrid();
                    tab.activated = true;
                    if (!arrayHelpers.isEmpty(tab.options)) {
                        var option = tab.options.find(function(option) {
                            return option.breakdown === tab.breakdown;
                        });
                        if (option) {
                            mapFromTo(tab, option);
                        }
                    }
                });
            } else {
                if (tab.shouldRefresh) {
                    tab.grid.api.reload();
                }
                $timeout(function() {
                    tab.grid.api.refreshUI();
                }, 100);
            }
            tab.shouldRefresh = false;
        }

        function markOtherTabsForRefresh() {
            var currentTab = getTab($ctrl.breakdown);
            $ctrl.tabs.forEach(function(tab) {
                tab.shouldRefresh = true;
            });
            currentTab.shouldRefresh = false;
        }

        function selectTab(tab) {
            $ctrl.tabs.forEach(function(tab) {
                tab.selected = false;
            });
            tab.selected = true;
        }

        function getTab(breakdown) {
            var tabToActivate = $ctrl.tabs.find(function(tab) {
                return tab.breakdown === breakdown;
            });
            if (tabToActivate) {
                return tabToActivate;
            }

            for (var index = 0; index < $ctrl.tabs.length; index++) {
                if (!arrayHelpers.isEmpty($ctrl.tabs[index].options)) {
                    var option = $ctrl.tabs[index].options.find(function(
                        option
                    ) {
                        return option.breakdown === breakdown;
                    });
                    if (option) {
                        zemLocalStorageService.set(
                            $ctrl.tabs[index].localStorageKey,
                            breakdown,
                            LOCAL_STORAGE_KEY_NAMESPACE
                        );
                        mapFromTo(option, $ctrl.tabs[index]);
                        return $ctrl.tabs[index];
                    }
                }
            }

            return tabToActivate;
        }

        function mapFromTo(from, to) {
            to.name = from.name;
            to.breakdown = from.breakdown;
            to.gridIntegrationService = from.gridIntegrationService;
            to.grid = from.grid;
            to.activated = from.activated;
            to.selected = from.selected;
            to.isNewFeature = from.isNewFeature || false;
        }

        function onGridInitialized(tab, gridApi) {
            tab.gridIntegrationService.setGridApi(gridApi);

            zemBidModifierUpdatesService
                .getAllUpdates$()
                .subscribe(markOtherTabsForRefresh);
        }
    },
});
