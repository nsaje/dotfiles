angular
    .module('one.services')
    .service('zemCampaignBudgetsEndpoint', function($http, $q) {
        this.list = list;
        this.create = create;
        this.save = save;
        this.get = get;

        function list(campaignId) {
            var url = '/api/campaigns/' + campaignId + '/budget/';
            return $http
                .get(url)
                .then(processResponse)
                .then(function(data) {
                    if (data === null) {
                        return null;
                    }
                    return {
                        active: data.active.map(convertDataFromApi),
                        past: data.past.map(convertDataFromApi),
                        totals: {
                            currentAvailable: data.totals.current.available,
                            currentUnallocated: data.totals.current.unallocated,
                            lifetimeCampaignSpend:
                                data.totals.lifetime.campaign_spend,
                            lifetimeMediaSpend:
                                data.totals.lifetime.media_spend,
                            lifetimeDataSpend: data.totals.lifetime.data_spend,
                            lifetimeLicenseFee:
                                data.totals.lifetime.license_fee,
                            lifetimeMargin: data.totals.lifetime.margin,
                            currencySymbol:
                                constants.currencySymbol[data.totals.currency],
                        },
                        credits: data.credits.map(function(obj) {
                            return {
                                licenseFee: obj.license_fee,
                                total: obj.total,
                                available: obj.available,
                                startDate: moment(
                                    obj.start_date,
                                    'YYYY-MM-DD'
                                ).format('MM/DD/YYYY'),
                                endDate: moment(
                                    obj.end_date,
                                    'YYYY-MM-DD'
                                ).format('MM/DD/YYYY'),
                                currencySymbol:
                                    constants.currencySymbol[obj.currency],
                                id: obj.id,
                                comment: obj.comment,
                                isAvailable: obj.is_available,
                                isAgency: obj.is_agency,
                            };
                        }),
                    };
                });
        }

        function create(campaignId, budget) {
            var url = '/api/campaigns/' + campaignId + '/budget/';
            return $http
                .put(url, convertDataToApi(budget))
                .then(processResponse, processError);
        }

        function save(campaignId, budget) {
            var url =
                '/api/campaigns/' + campaignId + '/budget/' + budget.id + '/';
            return $http
                .post(url, convertDataToApi(budget))
                .then(processResponse, processError)
                .then(function(data) {
                    return {
                        id: data.id,
                    };
                });
        }

        function get(campaignId, budgetId) {
            var url =
                '/api/campaigns/' + campaignId + '/budget/' + budgetId + '/';
            return $http
                .get(url)
                .then(processResponse)
                .then(convertDataFromApi);
        }

        function convertDataFromApi(obj) {
            return {
                id: obj.id,
                credit: obj.credit,
                amount: obj.amount,
                startDate: moment(obj.start_date, 'YYYY-MM-DD').format(
                    'MM/DD/YYYY'
                ),
                endDate: moment(obj.end_date, 'YYYY-MM-DD').format(
                    'MM/DD/YYYY'
                ),
                currencySymbol: constants.currencySymbol[obj.currency],
                total: obj.total || obj.amount,
                licenseFee: obj.license_fee,
                createdBy: obj.created_by,
                createdOn: moment(obj.created_at).format('MM/DD/YYYY'),
                spend: obj.spend,
                state: obj.state,
                isEditable: obj.is_editable,
                isUpdatable: obj.is_updatable,
                available: obj.available,
                margin: obj.margin,
                comment: obj.comment,
            };
        }

        function convertDataToApi(obj) {
            return {
                credit: obj.credit.id,
                amount: obj.amount,
                start_date: moment(obj.startDate).format('YYYY-MM-DD'),
                end_date: moment(obj.endDate).format('YYYY-MM-DD'),
                margin: obj.margin,
                comment: obj.comment,
            };
        }

        function processResponse(resp) {
            return resp.data.success ? resp.data.data : null;
        }

        function processError(resp) {
            return $q.reject(convertError(resp));
        }

        function convertError(resp) {
            if (!resp.data.data.errors) {
                return null;
            }
            return {
                amount: resp.data.data.errors.amount,
                startDate: resp.data.data.errors.start_date,
                endDate: resp.data.data.errors.end_date,
                margin: resp.data.data.errors.margin,
                comment: resp.data.data.errors.comment,
                credit: resp.data.data.errors.credit,
            };
        }
    });
