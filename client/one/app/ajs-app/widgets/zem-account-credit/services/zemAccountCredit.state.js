angular
    .module('one.widgets')
    .service('zemAccountCreditStateService', function(
        zemAccountCreditEndpoint,
        zemAccountCreditRefundEndpoint,
        zemUserService,
        $q,
        $filter
    ) {
        // eslint-disable-line max-len
        this.createInstance = createInstance;

        function createInstance(account) {
            return new zemAccountCreditStateService(account);
        }

        function zemAccountCreditStateService(account) {
            this.getState = getState;
            this.reloadCredit = reloadCredit;
            this.createNewCreditItem = createNewCreditItem;
            this.reloadCreditItem = reloadCreditItem;
            this.saveCreditItem = saveCreditItem;
            this.cancelCreditItem = cancelCreditItem;
            this.clearCreditItem = clearCreditItem;
            this.setCreditItem = setCreditItem;
            this.reloadCreditRefunds = reloadCreditRefunds;
            this.clearCreditRefundItem = clearCreditRefundItem;
            this.saveCreditRefundItem = saveCreditRefundItem;

            var state = {
                credit: {},
                creditRefunds: {},
                creditRefundTotals: {},
                creditItem: {},
                creditRefundItem: {},
                requests: {
                    reloadCredit: {},
                    reloadCreditRefunds: {},
                    reloadCreditItem: {},
                    saveCreditItem: {},
                    cancelCreditItem: {},
                    saveCreditRefundItem: {},
                },
            };

            function getState() {
                return state;
            }

            function reloadCredit() {
                state.credit = {};
                state.creditRefundTotals = {};
                state.requests.reloadCredit = {};

                if (!account) return $q.reject();

                state.requests.reloadCredit.inProgress = true;
                return zemAccountCreditEndpoint
                    .list(account.id)
                    .then(function(data) {
                        state.credit = data;
                        reloadCreditRefunds();
                    })
                    .finally(function() {
                        state.requests.reloadCredit.inProgress = false;
                    });
            }

            function clearCreditItem() {
                state.creditItem = {};
                state.requests.reloadCreditItem = {};
                state.requests.saveCreditItem = {};
            }

            function createNewCreditItem(currentMoment) {
                state.creditItem = {
                    createdBy: zemUserService.current().name,
                    createdOn: currentMoment.format('MM/DD/YYYY'),
                    startDate: currentMoment.toDate(),
                };
            }

            function reloadCreditItem(id) {
                state.creditItem = {};
                state.requests.reloadCreditItem = {};

                if (!account || !id) return $q.reject();

                state.requests.reloadCreditItem.inProgress = true;
                return zemAccountCreditEndpoint
                    .get(account.id, id)
                    .then(function(data) {
                        state.creditItem = data;
                        state.creditItem.startDate = moment(
                            data.startDate,
                            'MM/DD/YYYY'
                        ).toDate();
                        state.creditItem.endDate = moment(
                            data.endDate,
                            'MM/DD/YYYY'
                        ).toDate();
                        state.creditItem.licenseFee = $filter('number')(
                            data.licenseFee.replace('%', ''),
                            2
                        );
                    })
                    .finally(function() {
                        state.requests.reloadCreditItem.inProgress = false;
                    });
            }

            function saveCreditItem(isNew) {
                state.requests.saveCreditItem = {};

                if (!account || !state.creditItem) return $q.reject();

                var action = zemAccountCreditEndpoint.update;
                if (isNew) {
                    action = zemAccountCreditEndpoint.create;
                }

                state.requests.saveCreditItem.inProgress = true;
                return action(account.id, state.creditItem)
                    .then(reloadCredit)
                    .catch(function(errors) {
                        state.requests.saveCreditItem.errors = errors;
                        return $q.reject();
                    })
                    .finally(function() {
                        state.requests.saveCreditItem.inProgress = false;
                    });
            }

            function cancelCreditItem(id) {
                state.requests.cancelCreditItem = {};

                if (!account || !id) return $q.reject();

                state.requests.cancelCreditItem.inProgress = true;
                return zemAccountCreditEndpoint
                    .cancel(account.id, [id])
                    .then(reloadCredit)
                    .finally(function() {
                        state.requests.cancelCreditItem.inProgress = false;
                    });
            }

            function setCreditItem(creditItem) {
                state.creditItem = creditItem;
            }

            function reloadCreditRefunds() {
                state.creditRefunds = {};
                state.creditRefundTotals = {};
                state.requests.reloadCreditRefunds = {};

                if (!account) return $q.reject();

                state.requests.reloadCreditRefunds.inProgress = true;
                return zemAccountCreditRefundEndpoint
                    .list(account.id)
                    .then(function(data) {
                        state.creditRefunds = mapCreditRefunds(data);
                        state.creditRefundTotals = calculateCreditRefundTotals();
                    })
                    .finally(function() {
                        state.requests.reloadCreditRefunds.inProgress = false;
                    });
            }

            function clearCreditRefundItem() {
                state.creditItem = {};
                state.creditRefundItem = {};
                state.requests.saveCreditRefundItem = {};
            }

            function saveCreditRefundItem() {
                state.requests.saveCreditRefundItem = {};

                if (!account || !state.creditItem || !state.creditRefundItem)
                    return $q.reject();

                var action = zemAccountCreditRefundEndpoint.create;
                state.requests.saveCreditRefundItem.inProgress = true;
                return action(
                    account.id,
                    state.creditItem.id,
                    state.creditRefundItem
                )
                    .then(reloadCreditRefunds)
                    .catch(function(errors) {
                        state.requests.saveCreditRefundItem.errors = errors;
                        return $q.reject();
                    })
                    .finally(function() {
                        state.requests.saveCreditRefundItem.inProgress = false;
                    });
            }

            function mapCreditRefunds(data) {
                return data.reduce(function(refunds, refund) {
                    if (refund.creditId in refunds) {
                        refunds[refund.creditId].push(refund);
                    } else {
                        refunds[refund.creditId] = [refund];
                    }
                    return refunds;
                }, {});
            }

            function calculateCreditRefundTotals() {
                var totals = {};
                var refunds = state.creditRefunds;
                var credits = state.credit.active
                    .concat(state.credit.past)
                    .reduce(function(creditMap, credit) {
                        creditMap[credit.id] = credit;
                        return creditMap;
                    }, {});
                Object.keys(refunds).forEach(function(creditId) {
                    totals[creditId] = refunds[creditId].reduce(function(
                        total,
                        refund
                    ) {
                        return total + parseInt(refund.amount);
                    },
                    parseInt(credits[creditId].total));
                });
                return totals;
            }
        }
    });
