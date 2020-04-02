describe('component: zemPublisherGroupsUpload', function() {
    var $ctrl;
    var zemPublisherGroupsEndpoint;
    var bindings;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.downgradedProviders'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));

    beforeEach(inject(function(
        $componentController,
        _zemPublisherGroupsEndpoint_
    ) {
        zemPublisherGroupsEndpoint = _zemPublisherGroupsEndpoint_;
        bindings = {
            resolve: {
                account: {
                    id: '1',
                },
            },
            modalInstance: {},
        };
        $ctrl = $componentController('zemPublisherGroupsUpload', {}, bindings);
    }));

    describe('update mode', function() {
        beforeEach(function() {
            bindings.resolve.publisherGroup = {
                id: 1,
                name: 'asd',
                include_subdomains: false,
            };
        });

        it('should initialize update mode', function() {
            $ctrl.$onInit();

            expect($ctrl.isCreationMode).toBe(false);
            expect($ctrl.formData).toEqual({
                id: 1,
                name: 'asd',
                include_subdomains: false,
                scopeState: 'ACCOUNT_SCOPE',
                agencyId: null,
                accountId: '1',
            });
        });

        it('should initialize update mode for agency', function() {
            bindings.resolve.publisherGroup.agency_id = 123;
            $ctrl.$onInit();

            expect($ctrl.isCreationMode).toBe(false);
            expect($ctrl.formData).toEqual({
                id: 1,
                name: 'asd',
                include_subdomains: false,
                scopeState: 'AGENCY_SCOPE',
                agencyId: 123,
                accountId: '1',
            });
        });

        it('should properly call the upsert endpoint for update', function() {
            $ctrl.$onInit();
            spyOn(zemPublisherGroupsEndpoint, 'upsert').and.callThrough();
            $ctrl.upsert();

            expect(zemPublisherGroupsEndpoint.upsert).toHaveBeenCalledWith({
                id: 1,
                name: 'asd',
                include_subdomains: false,
                scopeState: 'ACCOUNT_SCOPE',
                agencyId: null,
                accountId: '1',
            });
        });
    });

    describe('create new mode', function() {
        beforeEach(function() {
            bindings.resolve.publisherGroup = undefined;
        });

        it('should initialize create mode', function() {
            $ctrl.$onInit();

            expect($ctrl.formData).toEqual({
                include_subdomains: true,
                scopeState: 'ACCOUNT_SCOPE',
                agencyId: null,
                accountId: '1',
            });
            expect($ctrl.isCreationMode).toBe(true);
        });

        it('should properly call the upsert endpoint for create new', function() {
            $ctrl.$onInit();
            spyOn(zemPublisherGroupsEndpoint, 'upsert').and.callThrough();
            $ctrl.formData.name = 'asd';
            $ctrl.upsert();

            expect(zemPublisherGroupsEndpoint.upsert).toHaveBeenCalledWith({
                name: 'asd',
                include_subdomains: true,
                scopeState: 'ACCOUNT_SCOPE',
                agencyId: null,
                accountId: '1',
            });
        });
    });

    describe('handle errors', function() {
        beforeEach(function() {
            $ctrl.errors = {
                name: 'a',
                entries: 'b',
                errors_csv_key: 'c',
            };
        });

        it('should clear name error', function() {
            $ctrl.clearValidationError('name');

            expect($ctrl.errors).toEqual({
                entries: 'b',
                errors_csv_key: 'c',
            });
        });

        it('should clear entries error', function() {
            $ctrl.clearValidationError('entries');

            expect($ctrl.errors).toEqual({
                name: 'a',
            });
        });
    });
});
