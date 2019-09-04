angular
    .module('one.widgets')
    .service('zemReportFieldsService', function(zemPermissions) {
        // eslint-disable-line max-len
        var ALWAYS_FIELDS = {
            ad_groups: ['Account', 'Campaign', 'Ad Group'],
            campaigns: ['Account', 'Campaign'],
            accounts: ['Account'],
            all_accounts: [],
        };

        var REMAPPED_FIELDS = {
            Thumbnail: ['Image Hash', 'Image URL', 'Ad Tag'],
        };

        if (zemPermissions.hasPermission('zemauth.can_use_creative_icon')) {
            REMAPPED_FIELDS.Thumbnail.push('Icon Image Hash', 'Icon Image URL');
        }

        var FIELDS_WITH_IDS = [
            'Content Ad',
            'Ad Group',
            'Campaign',
            'Account',
            'Agency',
        ];

        var FIELDS_WITH_STATUSES = [
            'Account',
            'Campaign',
            'Ad Group',
            'Content Ad',
            'Publisher',
        ];

        var COLUMNS_TO_REMOVE = ['Actions'];

        // Public API
        this.getFields = getFields;

        function getFields(
            gridLevel,
            gridBreakdown,
            breakdown,
            includeIds,
            selectedFields,
            togglableColumns,
            gridFields
        ) {
            var fields = angular.copy(ALWAYS_FIELDS[gridLevel]);
            if (
                zemPermissions.hasPermission(
                    'zemauth.can_view_account_agency_information'
                ) &&
                fields.indexOf('Account') >= 0
            ) {
                fields.unshift('Agency');
            }

            for (var i = 0; i < breakdown.length; i++) {
                fields.push(breakdown[i].report_query);
            }

            fields = fields.concat(gridFields);
            fields = filterOutClientOnlyFields(fields);
            fields = addIdFields(fields, includeIds);
            fields = addStatusFields(fields, gridLevel, gridBreakdown);

            if (gridLevel === 'ad_groups' && gridBreakdown === 'publisher') {
                fields.push('Source Slug');
            }

            fields = filterBySelectedFields(
                fields,
                selectedFields,
                togglableColumns
            );
            fields = remapFields(fields);
            fields = deduplicateFields(fields);

            return fields;
        }

        function filterBySelectedFields(
            fields,
            selectedFields,
            togglableColumns
        ) {
            // filter by selected fields
            var newFields = fields.filter(function(item) {
                if (!togglableColumns.includes(item)) {
                    // Keep extra fields (always fields, fields with statuses...)
                    return item;
                }
                // Keep selected fields
                return selectedFields.indexOf(item) !== -1;
            });

            for (var i = 0; i < selectedFields.length; i++) {
                if (!newFields.includes(selectedFields[i])) {
                    // Add additional selected fields
                    newFields.push(selectedFields[i]);
                }
            }

            return newFields;
        }

        function remapFields(fields) {
            var newFields = angular.copy(fields);
            for (var i = 0; i < fields.length; i++) {
                if (fields[i] in REMAPPED_FIELDS) {
                    newFields = newFields.concat(REMAPPED_FIELDS[fields[i]]);
                    newFields = newFields.filter(function(item) {
                        return item !== fields[i];
                    });
                }
            }
            return newFields;
        }

        function filterOutClientOnlyFields(fields) {
            var newFields = [];
            for (var i = 0; i < fields.length; i++) {
                if (COLUMNS_TO_REMOVE.indexOf(fields[i]) !== -1) {
                    continue;
                }
                newFields.push(fields[i]);
            }
            return newFields;
        }

        function deduplicateFields(fields) {
            var newFields = [];
            for (var i = 0; i < fields.length; i++) {
                if (newFields.indexOf(fields[i]) < 0) {
                    newFields.push(fields[i]);
                }
            }
            return newFields;
        }

        function addIdFields(fields, includeIds) {
            var newFields = [];
            for (var i = 0; i < fields.length; i++) {
                if (includeIds && FIELDS_WITH_IDS.indexOf(fields[i]) >= 0) {
                    newFields.push(fields[i] + ' ID');
                }
                newFields.push(fields[i]);
            }
            return newFields;
        }

        function addStatusFields(fields, level, breakdown) {
            var includeStatuses = fields.indexOf('Status') >= 0;
            var newFields = [];
            for (var i = 0; i < fields.length; i++) {
                if (fields[i] === 'Status') continue;
                newFields.push(fields[i]);
                if (includeStatuses) {
                    if (FIELDS_WITH_STATUSES.indexOf(fields[i]) >= 0) {
                        newFields.push(fields[i] + ' Status');
                    }
                    if (
                        level === 'ad_groups' &&
                        breakdown !== 'publisher' &&
                        fields[i] === 'Media Source'
                    ) {
                        newFields.push('Media Source Status');
                    }
                }
            }
            return newFields;
        }
    });
