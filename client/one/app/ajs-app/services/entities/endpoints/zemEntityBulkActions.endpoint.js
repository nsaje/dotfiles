angular
    .module('one.services')
    .service('zemEntityBulkActionsEndpoint', function($http, $q) {
        // eslint-disable-line max-len

        //
        // Public API
        //
        this.archive = archive;
        this.restore = restore;
        this.activate = activate;
        this.deactivate = deactivate;
        this.edit = edit;

        function archive(level, breakdown, parentId, selection) {
            return post(
                getUrl(level, breakdown, parentId, 'archive'),
                createSelectionData(selection)
            );
        }

        function restore(level, breakdown, parentId, selection) {
            return post(
                getUrl(level, breakdown, parentId, 'restore'),
                createSelectionData(selection)
            );
        }

        function activate(level, breakdown, parentId, selection) {
            var data = createSelectionData(selection);
            data.state = constants.settingsState.ACTIVE;
            return post(getUrl(level, breakdown, parentId, 'state'), data);
        }

        function deactivate(level, breakdown, parentId, selection) {
            var data = createSelectionData(selection);
            data.state = constants.settingsState.INACTIVE;
            return post(getUrl(level, breakdown, parentId, 'state'), data);
        }

        function edit(level, breakdown, parentId, selection) {
            var data = createSelectionData(selection);
            return post(getUrl(level, breakdown, parentId, 'edit'), data);
        }

        function createSelectionData(selection) {
            return {
                selected_ids: selection.selectedIds,
                not_selected_ids: selection.unselectedIds,
                select_all: selection.filterAll,
                select_batch: selection.filterId,
            };
        }

        function post(url, data) {
            var deferred = $q.defer();

            $http
                .post(url, data)
                .success(function(data) {
                    deferred.resolve(data);
                })
                .error(function(data) {
                    deferred.reject(data);
                });

            return deferred.promise;
        }

        var breakdownUrlMap = {};
        breakdownUrlMap[constants.breakdown.ACCOUNT] = 'accounts';
        breakdownUrlMap[constants.breakdown.CAMPAIGN] = 'campaigns';
        breakdownUrlMap[constants.breakdown.AD_GROUP] = 'ad_groups';
        breakdownUrlMap[constants.breakdown.CONTENT_AD] = 'contentads';
        breakdownUrlMap[constants.breakdown.MEDIA_SOURCE] = 'sources';

        function getUrl(level, breakdown, id, action) {
            if (level === constants.level.ALL_ACCOUNTS) {
                return (
                    '/api/' +
                    level +
                    '/' +
                    breakdownUrlMap[breakdown] +
                    '/' +
                    action +
                    '/'
                );
            }

            return (
                '/api/' +
                level +
                '/' +
                id +
                '/' +
                breakdownUrlMap[breakdown] +
                '/' +
                action +
                '/'
            );
        }
    });
