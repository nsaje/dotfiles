angular.module('one.widgets').service('zemReportFieldsService', function (zemPermissions) {  // eslint-disable-line max-len
    var ALWAYS_FIELDS = {
        ad_groups: ['Account', 'Campaign', 'Ad Group'],
        campaigns: ['Account', 'Campaign'],
        accounts: ['Account'],
        all_accounts: [],
    };

    var HIDDEN_TYPES = ['stateSelector', 'submissionStatus'];

    var REMAPPED_FIELDS = {
        'Thumbnail': ['Image Hash', 'Image URL'],
    };

    var FIELDS_WITH_IDS = ['Content Ad', 'Ad Group', 'Campaign', 'Account', 'Agency'];
    var FIELDS_WITH_STATUSES = ['Account', 'Campaign', 'Ad Group', 'Content Ad', 'Publisher'];

    var BREAKDOWN_REQUIRED_FIELDS = {
        'content_ad': ['URL', 'Thumbnail', 'Brand Name', 'Description', 'Label', 'Call to action', 'Impression trackers'],
    };

    var COLUMNS_TO_REMOVE = ['Actions'];

    // Public API
    this.getFields = getFields;

    function getFields (gridApi, breakdown, includeIds) {

        var fields = angular.copy(ALWAYS_FIELDS[gridApi.getMetaData().level]);
        if (zemPermissions.hasPermission('zemauth.can_view_account_agency_information') &&
                fields.indexOf('Account') >= 0) {
            fields.unshift('Agency');
        }

        for (var i = 0; i < breakdown.length; i++) {
            fields.push(breakdown[i].report_query);
            fields = addBreakdownRequiredFields(fields, breakdown[i].query);
        }

        fields = fields.concat(getGridFields(gridApi));

        fields = filterOutClientOnlyFields(fields);
        fields = remapFields(fields);

        fields = addIdFields(fields, includeIds);
        fields = addStatusFields(fields, gridApi.getMetaData().level, gridApi.getMetaData().breakdown);

        fields = deduplicateFields(fields);

        return fields;
    }

    function getGridFields (gridApi) {
        return gridApi.getColumns()
            .filter(function (column) { return column.visible; })
            .filter(function (column) { return !column.disabled; })
            .filter(function (column) { return column.data.name; })
            .filter(function (column) { return HIDDEN_TYPES.indexOf(column.data.type) < 0; })
            .map(function (column) { return column.data.name; });
    }

    function remapFields (fields) {
        var newFields = [];
        for (var i = 0; i < fields.length; i++) {
            if (fields[i] in REMAPPED_FIELDS) {
                newFields = newFields.concat(REMAPPED_FIELDS[fields[i]]);
            } else {
                newFields.push(fields[i]);
            }
        }
        return newFields;
    }

    function addBreakdownRequiredFields (fields, breakdown) {
        return fields.concat(BREAKDOWN_REQUIRED_FIELDS[breakdown] || []);
    }

    function filterOutClientOnlyFields (fields) {
        var newFields = [];
        for (var i = 0; i < fields.length; i++) {
            if (COLUMNS_TO_REMOVE.indexOf(fields[i]) !== -1) {
                continue;
            }
            newFields.push(fields[i]);
        }
        return newFields;
    }

    function deduplicateFields (fields) {
        var newFields = [];
        for (var i = 0; i < fields.length; i++) {
            if (newFields.indexOf(fields[i]) < 0) {
                newFields.push(fields[i]);
            }
        }
        return newFields;
    }

    function addIdFields (fields, includeIds) {
        var newFields = [];
        for (var i = 0; i < fields.length; i++) {
            if (includeIds && FIELDS_WITH_IDS.indexOf(fields[i]) >= 0) {
                newFields.push(fields[i] + ' ID');
            }
            newFields.push(fields[i]);
        }
        return newFields;
    }

    function addStatusFields (fields, level, breakdown) {
        var includeStatuses = fields.indexOf('Status') >= 0;
        var newFields = [];
        for (var i = 0; i < fields.length; i++) {
            if (fields[i] === 'Status') continue;
            newFields.push(fields[i]);
            if (includeStatuses) {
                if (FIELDS_WITH_STATUSES.indexOf(fields[i]) >= 0) {
                    newFields.push(fields[i] + ' Status');
                }
                if (level === 'ad_groups' && breakdown !== 'publisher' && fields[i] === 'Media Source') {
                    newFields.push('Media Source Status');
                }
            }
        }
        return newFields;
    }
});
