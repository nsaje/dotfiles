angular
    .module('one.widgets')
    .directive('zemGridCellBidModifierField', function() {
        return {
            restrict: 'E',
            replace: true,
            scope: {},
            controllerAs: 'ctrl',
            bindToController: {
                data: '=',
                column: '=',
                row: '=',
                grid: '=',
            },
            template: require('./zemGridCellBidModifierField.component.html'),
            controller: function(
                $scope,
                zemGridConstants,
                zemGridDataFormatter,
                zemGridDataValidator,
                zemBidModifierApiService
            ) {
                var vm = this;
                var initialValue = '';
                var prevValidInputValue = '';

                var blacklistMap = invertBlacklistMap();

                vm.filterInput = filterInput;
                vm.onKeyDown = onKeyDown;
                vm.onButtonMinus = onButtonMinus;
                vm.onButtonPlus = onButtonPlus;
                vm.save = save;
                vm.closeModal = closeModal;
                vm.isEditable = true;

                vm.sign = '+';
                vm.delta = '0';
                vm.newCpc = '0';

                $scope.$watch('ctrl.row', update);
                $scope.$watch('ctrl.data', update, true);

                // returns a map from text constants to numbers
                function invertBlacklistMap() {
                    return Object.keys(constants.publisherStatus).reduce(
                        function(obj, key) {
                            obj[constants.publisherStatus[key]] = key;
                            return obj;
                        },
                        {}
                    );
                }

                function update() {
                    vm.formattedValue = '';
                    vm.class = vm.column.type + '-field';

                    vm.isEditable = true;
                    if (!isFieldVisible()) {
                        vm.isEditable = false;
                        return;
                    }

                    var formatterOptions = angular.copy(vm.column.data);
                    formatterOptions.defaultValue = '0.00%';
                    formatterOptions.currency = vm.grid.meta.data.ext.currency;
                    vm.currencySymbol = zemGridDataFormatter.getCurrencySymbol(
                        formatterOptions
                    );

                    if (vm.data) {
                        vm.isEditable = vm.data.isEditable;
                        vm.editMessage = vm.data.editMessage;
                    }

                    if (!vm.data || !vm.data.value) {
                        vm.sourceBidCpc = undefined;
                        value = undefined;
                    } else {
                        vm.sourceBidCpc = vm.data.value.source_bid_value
                            ? vm.data.value.source_bid_value.bid_cpc_value
                            : undefined;

                        var value = vm.data.value.modifier
                            ? vm.data.value.modifier
                            : undefined;
                    }

                    vm.formattedValue = zemGridDataFormatter.formatValue(
                        value,
                        formatterOptions
                    );

                    if (vm.isEditable) {
                        initialValue = isNaN(value)
                            ? (0.0).toFixed(2)
                            : (value * 100 - 100).toFixed(2);
                        prevValidInputValue = initialValue;
                        vm.editFormInputValue = prevValidInputValue;
                    }

                    formatDisplay();
                }

                function isFieldVisible() {
                    if (!vm.row || !vm.column) {
                        return false;
                    }
                    if (
                        vm.row.level === zemGridConstants.gridRowLevel.FOOTER &&
                        vm.column.data.totalRow === false
                    ) {
                        return false;
                    }
                    return true;
                }

                function formatDisplay() {
                    if (['', '+', '-'].indexOf(prevValidInputValue) + 1) {
                        vm.sign = '+';
                        vm.delta = (0.0).toFixed(2);
                        vm.newCpc = vm.sourceBidCpc;
                    } else {
                        var validValue = parseFloat(prevValidInputValue);
                        if (validValue < 0) {
                            vm.sign = '−';
                        } else {
                            vm.sign = '+';
                        }
                        vm.delta = (
                            Math.abs(validValue / 100.0) *
                            parseFloat(vm.sourceBidCpc)
                        ).toFixed(2);
                        vm.newCpc = (
                            parseFloat(vm.sourceBidCpc) +
                            (validValue / 100.0) * parseFloat(vm.sourceBidCpc)
                        ).toFixed(2);
                    }
                }

                function filterInput() {
                    var newValue = parseFloat(vm.editFormInputValue);
                    var isEmptyOrSign =
                        ['', '+', '-'].indexOf(vm.editFormInputValue) + 1;
                    if (
                        (isNaN(newValue) && !isEmptyOrSign) ||
                        newValue < -99 ||
                        newValue > 1000
                    ) {
                        vm.editFormInputValue = prevValidInputValue;
                    } else {
                        prevValidInputValue = vm.editFormInputValue;
                    }

                    formatDisplay();
                }

                function modifyInput(deltaPercent) {
                    var oldValue = parseFloat(vm.editFormInputValue);
                    if (isNaN(oldValue)) {
                        oldValue = 0.0;
                    }
                    var newValue = oldValue + deltaPercent;
                    vm.editFormInputValue = newValue.toFixed(2);
                    filterInput();
                }

                function onButtonPlus() {
                    modifyInput(1);
                }

                function onButtonMinus() {
                    modifyInput(-1);
                }

                function onKeyDown($event) {
                    if ($event.keyCode === 13) save(); // Enter
                    if ($event.keyCode === 27) closeModal(); // ESC
                }

                function save() {
                    if (prevValidInputValue === initialValue) {
                        closeModal();
                        return;
                    }

                    vm.showLoader = true;

                    var adGroupId = vm.grid.meta.data.id;

                    var sourceSlug = vm.row.data.stats.source_slug.value;
                    var pubDomain = vm.row.data.stats.domain.value;
                    var blacklistStatus = vm.row.data.stats.status.value;

                    blacklistStatus = blacklistMap[blacklistStatus];

                    var newModifier =
                        (parseFloat(prevValidInputValue) + 100) / 100.0;

                    zemBidModifierApiService
                        .setBidModifier(
                            adGroupId,
                            sourceSlug,
                            pubDomain,
                            blacklistStatus,
                            newModifier
                        )
                        .then(function(response) {
                            vm.data.value.modifier =
                                response.data.data[0].modifier;
                            vm.showLoader = false;
                            closeModal();
                        })
                        .catch(function(response) {
                            vm.showLoader = false;
                            return response;
                        });
                }

                function closeModal() {
                    if (vm.modal && vm.modal.close) {
                        vm.modal.close();
                    }
                }
            },
        };
    });
