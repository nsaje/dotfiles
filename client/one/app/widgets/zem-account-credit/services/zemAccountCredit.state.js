angular.module('one.widgets').service('zemAccountCreditStateService', function (zemAccountCreditEndpoint, zemUserService, $q, $filter) { // eslint-disable-line max-len
    this.createInstance = createInstance;

    function createInstance (account) {
        return new zemAccountCreditStateService(account);
    }

    function zemAccountCreditStateService (account) {
        this.getState = getState;
        this.reloadCredit = reloadCredit;
        this.createNewCreditItem = createNewCreditItem;
        this.reloadCreditItem = reloadCreditItem;
        this.saveCreditItem = saveCreditItem;
        this.cancelCreditItem = cancelCreditItem;
        this.clearCreditItem = clearCreditItem;

        var state = {
            credit: {},
            creditItem: {},
            requests: {
                reloadCredit: {},
                reloadCreditItem: {},
                saveCreditItem: {},
                cancelCreditItem: {},
            },
        };

        function getState () {
            return state;
        }

        function reloadCredit () {
            state.credit = {};
            state.requests.reloadCredit = {};

            if (!account) return $q.reject();

            state.requests.reloadCredit.inProgress = true;
            return zemAccountCreditEndpoint.list(account.id)
                .then(function (data) {
                    state.credit = data;
                })
                .finally(function () {
                    state.requests.reloadCredit.inProgress = false;
                });
        }

        function clearCreditItem () {
            state.creditItem = {};
            state.requests.reloadCreditItem = {};
            state.requests.saveCreditItem = {};
        }

        function createNewCreditItem (currentMoment) {
            state.creditItem = {
                createdBy: zemUserService.current().name,
                createdOn: currentMoment.format('MM/DD/YYYY'),
                startDate: currentMoment.toDate(),
            };
        }

        function reloadCreditItem (id) {
            state.creditItem = {};
            state.requests.reloadCreditItem = {};

            if (!account || !id) return $q.rejcet();

            state.requests.reloadCreditItem.inProgress = true;
            return zemAccountCreditEndpoint.get(account.id, id)
                .then(function (data) {
                    state.creditItem = data;
                    state.creditItem.startDate = moment(data.startDate, 'MM/DD/YYYY').toDate();
                    state.creditItem.endDate = moment(data.endDate, 'MM/DD/YYYY').toDate();
                    state.creditItem.licenseFee = $filter('number')(data.licenseFee.replace('%', ''), 2);
                })
                .finally(function () {
                    state.requests.reloadCreditItem.inProgress = false;
                });
        }

        function saveCreditItem (isNew) {
            state.requests.saveCreditItem = {};

            if (!account || !state.creditItem) return $q.rejcet();

            var action = zemAccountCreditEndpoint.update;
            if (isNew) {
                action = zemAccountCreditEndpoint.create;
            }

            state.requests.saveCreditItem.inProgress = true;
            return action(account.id, state.creditItem)
                .then(reloadCredit)
                .catch(function (errors) {
                    state.requests.saveCreditItem.errors = errors;
                    return $q.reject();
                })
                .finally(function () {
                    state.requests.saveCreditItem.inProgress = false;
                });
        }


        function cancelCreditItem (id) {
            state.requests.cancelCreditItem = {};

            if (!account || !id) return $q.rejcet();

            state.requests.cancelCreditItem.inProgress = true;
            return zemAccountCreditEndpoint.cancel(account.id, [id])
                .then(reloadCredit)
                .finally(function () {
                    state.requests.cancelCreditItem.inProgress = false;
                });
        }
    }
});
