var commonHelpers = require('../../../../shared/helpers/common.helpers');
var ScopeSelectorState = require('../../../../shared/components/scope-selector/scope-selector.constants')
    .ScopeSelectorState;
var CreditStatus = require('../../../../app.constants').CreditStatus;

angular
    .module('one.widgets')
    .service('zemCreditsStateService', function(
        zemAccountService,
        zemCreditsEndpoint,
        zemCreditsRefundEndpoint,
        zemUserService,
        zemPermissions,
        $q
    ) {
        this.createInstance = createInstance;

        function createInstance(agencyId, accountId) {
            return new zemCreditsStateService(agencyId, accountId);
        }

        function zemCreditsStateService(agencyId, accountId) {
            this.getState = getState;
            // credits
            this.reload = reload;
            this.reloadTotals = reloadTotals;
            this.reloadCredits = reloadCredits;
            this.reloadPastCredits = reloadPastCredits;
            this.saveCreditItem = saveCreditItem;
            this.cancelCreditItem = cancelCreditItem;
            this.clearCreditItem = clearCreditItem;
            this.setCreditItem = setCreditItem;
            // refunds
            this.reloadCreditRefunds = reloadCreditRefunds;
            this.clearCreditRefundItem = clearCreditRefundItem;
            this.saveCreditRefundItem = saveCreditRefundItem;
            this.setCreditRefundItem = setCreditRefundItem;

            var state = {
                agencyId: null,
                accountId: null,
                totals: [],
                credits: [],
                pastCredits: [],
                accounts: [],
                creditItem: {},
                creditItemScopeState: null,
                hasAgencyScope: false,
                creditRefunds: {},
                creditRefundTotals: {},
                creditRefundItem: {},
                requests: {
                    reloadTotals: {},
                    reloadCredits: {},
                    reloadPastCredits: {},
                    saveCreditItem: {},
                    cancelCreditItem: {},
                    reloadCreditRefunds: {},
                    saveCreditRefundItem: {},
                },
            };

            function init(agencyId, accountId) {
                state.agencyId = agencyId;
                state.accountId = accountId;
                state.hasAgencyScope = hasAgencyScope(state.agencyId);
                reloadAccounts();
            }

            function getState() {
                return state;
            }

            function reload() {
                $q.all([
                    reloadTotals(),
                    reloadCredits(),
                    reloadPastCredits(),
                ]).then(function() {
                    reloadCreditRefunds();
                });
            }

            function reloadTotals() {
                state.totals = [];
                state.requests.reloadTotals = {};

                if (!state.agencyId && !state.accountId) {
                    return $q.reject();
                }

                state.requests.reloadTotals.inProgress = true;
                return zemCreditsEndpoint
                    .totals(state.agencyId, state.accountId)
                    .then(function(data) {
                        state.totals = data;
                    })
                    .finally(function() {
                        state.requests.reloadTotals.inProgress = false;
                    });
            }

            function reloadCredits() {
                state.credit = [];
                state.requests.reloadCredits = {};

                if (!state.agencyId && !state.accountId) {
                    return $q.reject();
                }

                state.requests.reloadCredits.inProgress = true;
                return zemCreditsEndpoint
                    .listActive(state.agencyId, state.accountId)
                    .then(function(data) {
                        state.credits = data.map(function(creditItem) {
                            creditItem.isReadOnly = isReadOnly(creditItem);
                            return creditItem;
                        });
                    })
                    .finally(function() {
                        state.requests.reloadCredits.inProgress = false;
                    });
            }

            function reloadPastCredits() {
                state.pastCredits = [];
                state.requests.reloadPastCredits = {};

                if (!state.agencyId && !state.accountId) {
                    return $q.reject();
                }

                state.requests.reloadPastCredits.inProgress = true;
                return zemCreditsEndpoint
                    .listPast(state.agencyId, state.accountId)
                    .then(function(data) {
                        state.pastCredits = data;
                    })
                    .finally(function() {
                        state.requests.reloadPastCredits.inProgress = false;
                    });
            }

            function reloadAccounts() {
                state.accounts = [];
                state.requests.reloadAccounts = {};

                var subscription = null;
                if (commonHelpers.isDefined(state.agencyId)) {
                    state.requests.reloadAccounts.inProgress = true;
                    subscription = zemAccountService
                        .list(state.agencyId, function() {})
                        .subscribe(function(data) {
                            state.accounts = data;
                            state.requests.reloadAccounts.inProgress = false;
                            if (commonHelpers.isDefined(subscription)) {
                                subscription.unsubscribe();
                            }
                        });
                } else if (commonHelpers.isDefined(state.accountId)) {
                    subscription = zemAccountService
                        .get(state.accountId, function() {})
                        .subscribe(function(data) {
                            if (
                                commonHelpers.isNotEmpty(data) &&
                                commonHelpers.isNotEmpty(data.account)
                            ) {
                                state.accounts = [data.account];
                            }
                            state.requests.reloadAccounts.inProgress = false;
                            if (commonHelpers.isDefined(subscription)) {
                                subscription.unsubscribe();
                            }
                        });
                }
            }

            function clearCreditItem() {
                state.creditItem = {};
                (state.creditItemScopeState = null),
                    (state.requests.saveCreditItem = {});
            }

            function saveCreditItem() {
                state.requests.saveCreditItem = {};

                if (!commonHelpers.isDefined(state.creditItem)) {
                    return $q.reject();
                }

                var action = zemCreditsEndpoint.update;
                if (!commonHelpers.isDefined(state.creditItem.id)) {
                    action = zemCreditsEndpoint.create;
                }

                state.requests.saveCreditItem.inProgress = true;
                return action(state.creditItem)
                    .then(reloadCredits)
                    .catch(function(errors) {
                        state.requests.saveCreditItem.errors = (
                            errors.data || {}
                        ).details;
                        return $q.reject();
                    })
                    .finally(function() {
                        state.requests.saveCreditItem.inProgress = false;
                    });
            }

            function cancelCreditItem(creditItem) {
                state.requests.cancelCreditItem = {};

                if (
                    !commonHelpers.isDefined(creditItem) &&
                    !commonHelpers.isDefined(creditItem.id)
                ) {
                    return $q.reject();
                }

                creditItem = angular.copy(creditItem);
                creditItem.status = CreditStatus.CANCELED;

                state.requests.cancelCreditItem.inProgress = true;
                return zemCreditsEndpoint
                    .update(creditItem)
                    .then(reloadCredits)
                    .finally(function() {
                        state.requests.cancelCreditItem.inProgress = false;
                    });
            }

            function setCreditItem(creditItem) {
                if (!commonHelpers.isNotEmpty(creditItem)) {
                    var currentMoment = moment();
                    creditItem = {
                        createdBy: zemUserService.current().name,
                        createdOn: currentMoment.format('MM/DD/YYYY'),
                        startDate: currentMoment.toDate(),
                        endDate: null,
                        status: CreditStatus.PENDING,
                        isSigned: false,
                        isCanceled: false,
                    };
                } else {
                    creditItem = angular.copy(creditItem);
                    creditItem.startDate = moment(
                        creditItem.startDate,
                        'MM/DD/YYYY'
                    ).toDate();
                    creditItem.endDate = moment(
                        creditItem.endDate,
                        'MM/DD/YYYY'
                    ).toDate();
                }

                state.creditItem = creditItem;

                if (!commonHelpers.isDefined(state.creditItem.id)) {
                    if (
                        !commonHelpers.isDefined(state.accountId) &&
                        state.hasAgencyScope === true
                    ) {
                        state.creditItem.agencyId = state.agencyId;
                        state.creditItemScopeState =
                            ScopeSelectorState.AGENCY_SCOPE;
                    } else {
                        state.creditItem.accountId = state.accountId;
                        state.creditItemScopeState =
                            ScopeSelectorState.ACCOUNT_SCOPE;
                    }
                } else if (commonHelpers.isDefined(state.creditItem.agencyId)) {
                    state.creditItemScopeState =
                        ScopeSelectorState.AGENCY_SCOPE;
                } else {
                    state.creditItemScopeState =
                        ScopeSelectorState.ACCOUNT_SCOPE;
                }
            }

            function hasAgencyScope(agencyId) {
                return (
                    commonHelpers.isDefined(agencyId) &&
                    zemPermissions.hasAgencyScope(agencyId)
                );
            }

            function isReadOnly(creditItem) {
                if (
                    !state.hasAgencyScope &&
                    commonHelpers.isDefined(creditItem.agencyId)
                ) {
                    return true;
                }
                return false;
            }

            //
            // CREDIT REFUNDS
            //

            function reloadCreditRefunds() {
                state.creditRefunds = {};
                state.creditRefundTotals = {};
                state.requests.reloadCreditRefunds = {};

                if (!state.agencyId && !state.accountId) {
                    return $q.reject();
                }

                state.requests.reloadCreditRefunds.inProgress = true;
                return zemCreditsRefundEndpoint
                    .listAll(state.agencyId, state.accountId)
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
                state.creditItemScopeState = null;
                state.creditRefundItem = {};
                state.requests.saveCreditRefundItem = {};
            }

            function setCreditRefundItem(creditRefundItem) {
                if (!commonHelpers.isNotEmpty(creditRefundItem)) {
                    creditRefundItem = {
                        accountId:
                            state.creditItemScopeState ===
                            ScopeSelectorState.ACCOUNT_SCOPE
                                ? state.creditItem.accountId
                                : null,
                    };
                }
                state.creditRefundItem = creditRefundItem;
            }

            function saveCreditRefundItem() {
                state.requests.saveCreditRefundItem = {};

                if (!state.creditItem || !state.creditRefundItem) {
                    return $q.reject();
                }

                var action = zemCreditsRefundEndpoint.create;
                state.requests.saveCreditRefundItem.inProgress = true;
                return action(state.creditItem.id, state.creditRefundItem)
                    .then(reloadCreditRefunds)
                    .catch(function(errors) {
                        state.requests.saveCreditRefundItem.errors = (
                            errors.data || {}
                        ).details;
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
                var credits = state.credits
                    .concat(state.pastCredits)
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

            init(agencyId, accountId);
        }
    });
