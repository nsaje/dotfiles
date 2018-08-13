describe('zemGridOrderService', function() {
    var $rootScope;
    var zemGridConstants;
    var zemGridObject;
    var zemGridPubSub;
    var zemGridOrderService;
    var zemGridStorageService;

    beforeEach(angular.mock.module('one'));
    beforeEach(angular.mock.module('one.mocks.zemInitializationService'));
    beforeEach(angular.mock.module('one.mocks.NgZone'));

    beforeEach(
        angular.mock.module(function($provide) {
            $provide.value('zemGridStorageService', {
                saveOrder: angular.noop,
                loadOrder: angular.noop,
            });
            $provide.value('zemGridUIService', {
                resizeGridColumns: angular.noop,
            });
        })
    );

    beforeEach(inject(function(
        _$rootScope_,
        _zemGridConstants_,
        _zemGridObject_,
        _zemGridPubSub_,
        _zemGridOrderService_,
        _zemGridStorageService_
    ) {
        // eslint-disable-line max-len
        $rootScope = _$rootScope_;
        zemGridConstants = _zemGridConstants_;
        zemGridObject = _zemGridObject_;
        zemGridPubSub = _zemGridPubSub_;
        zemGridOrderService = _zemGridOrderService_;
        zemGridStorageService = _zemGridStorageService_;
    }));

    function createGrid() {
        var grid = zemGridObject.createGrid();
        var scope = $rootScope.$new();

        grid.meta.scope = scope;
        grid.meta.pubsub = zemGridPubSub.createInstance(scope);
        grid.meta.data = {};
        grid.meta.dataService = {
            getOrder: function() {
                return '-orderField1';
            },
            setOrder: function() {},
        };

        grid.header.columns.push(
            zemGridObject.createColumn({
                field: 'field1',
                orderField: 'orderField1',
            })
        );
        grid.header.columns.push(
            zemGridObject.createColumn({
                field: 'field2',
            })
        );
        grid.header.columns.push(
            zemGridObject.createColumn({
                field: 'field3',
                orderField: 'orderField3',
            })
        );

        return grid;
    }

    it('should initialize column orders based on data service order', function() {
        var grid = createGrid();
        var pubsub = grid.meta.pubsub;
        var orderService = zemGridOrderService.createInstance(grid);
        expect(orderService.getColumnOrder(grid.header.columns[0])).toBe(
            undefined
        );
        expect(orderService.getColumnOrder(grid.header.columns[1])).toBe(
            undefined
        );
        expect(orderService.getColumnOrder(grid.header.columns[2])).toBe(
            undefined
        );

        spyOn(grid.meta.dataService, 'getOrder').and.returnValue('orderField1');
        pubsub.notify(pubsub.EVENTS.DATA_UPDATED);
        expect(orderService.getColumnOrder(grid.header.columns[0])).toBe(
            zemGridConstants.gridColumnOrder.ASC
        );
        expect(orderService.getColumnOrder(grid.header.columns[1])).toBe(
            zemGridConstants.gridColumnOrder.NONE
        );
        expect(orderService.getColumnOrder(grid.header.columns[2])).toBe(
            zemGridConstants.gridColumnOrder.NONE
        );

        grid.meta.dataService.getOrder.and.returnValue('field2');
        pubsub.notify(pubsub.EVENTS.DATA_UPDATED);
        expect(orderService.getColumnOrder(grid.header.columns[0])).toBe(
            zemGridConstants.gridColumnOrder.NONE
        );
        expect(orderService.getColumnOrder(grid.header.columns[1])).toBe(
            zemGridConstants.gridColumnOrder.ASC
        );
        expect(orderService.getColumnOrder(grid.header.columns[2])).toBe(
            zemGridConstants.gridColumnOrder.NONE
        );
    });

    it('should initialize order when meta data is updated', function() {
        var grid = createGrid();
        var pubsub = grid.meta.pubsub;
        spyOn(grid.meta.pubsub, 'register').and.callThrough();
        spyOn(grid.meta.pubsub, 'notify').and.callThrough();

        var orderService = zemGridOrderService.createInstance(grid);
        expect(grid.meta.pubsub.register).toHaveBeenCalledWith(
            pubsub.EVENTS.METADATA_UPDATED,
            jasmine.any(Object),
            jasmine.any(Function)
        ); // eslint-disable-line max-len
        expect(grid.meta.pubsub.register).toHaveBeenCalledWith(
            pubsub.EVENTS.DATA_UPDATED,
            jasmine.any(Object),
            jasmine.any(Function)
        ); // eslint-disable-line max-len

        pubsub.notify(pubsub.EVENTS.METADATA_UPDATED);
        expect(grid.meta.pubsub.notify).toHaveBeenCalledWith(
            pubsub.EVENTS.EXT_ORDER_UPDATED
        );
        expect(orderService.getColumnOrder(grid.header.columns[0])).toBe(
            zemGridConstants.gridColumnOrder.DESC
        );
        expect(orderService.getColumnOrder(grid.header.columns[1])).toBe(
            zemGridConstants.gridColumnOrder.NONE
        );
        expect(orderService.getColumnOrder(grid.header.columns[2])).toBe(
            zemGridConstants.gridColumnOrder.NONE
        );
    });

    it('should load order when meta data is updated for the first time', function() {
        var grid = createGrid();
        var pubsub = grid.meta.pubsub;
        zemGridOrderService.createInstance(grid);

        spyOn(zemGridStorageService, 'loadOrder');

        pubsub.notify(pubsub.EVENTS.METADATA_UPDATED);
        expect(zemGridStorageService.loadOrder).toHaveBeenCalled();

        zemGridStorageService.loadOrder.calls.reset();
        pubsub.notify(pubsub.EVENTS.METADATA_UPDATED);
        expect(zemGridStorageService.loadOrder).not.toHaveBeenCalled();
    });

    it('should save order configuration', function() {
        var grid = createGrid();
        var pubsub = grid.meta.pubsub;
        var orderService = zemGridOrderService.createInstance(grid);

        spyOn(zemGridStorageService, 'saveOrder');

        pubsub.notify(pubsub.EVENTS.METADATA_UPDATED);
        orderService.setColumnOrder(
            grid.header.columns[1],
            zemGridConstants.gridColumnOrder.ASC
        );
        expect(zemGridStorageService.saveOrder).toHaveBeenCalled();
    });

    it('should keep only one order active', function() {
        var grid = createGrid();
        var pubsub = grid.meta.pubsub;
        var orderService = zemGridOrderService.createInstance(grid);
        pubsub.notify(pubsub.EVENTS.METADATA_UPDATED);

        expect(orderService.getColumnOrder(grid.header.columns[0])).toBe(
            zemGridConstants.gridColumnOrder.DESC
        );
        expect(orderService.getColumnOrder(grid.header.columns[1])).toBe(
            zemGridConstants.gridColumnOrder.NONE
        );
        expect(orderService.getColumnOrder(grid.header.columns[2])).toBe(
            zemGridConstants.gridColumnOrder.NONE
        );

        orderService.setColumnOrder(
            grid.header.columns[1],
            zemGridConstants.gridColumnOrder.ASC
        );
        expect(orderService.getColumnOrder(grid.header.columns[0])).toBe(
            zemGridConstants.gridColumnOrder.NONE
        );
        expect(orderService.getColumnOrder(grid.header.columns[1])).toBe(
            zemGridConstants.gridColumnOrder.ASC
        );
        expect(orderService.getColumnOrder(grid.header.columns[2])).toBe(
            zemGridConstants.gridColumnOrder.NONE
        );

        orderService.setColumnOrder(
            grid.header.columns[2],
            zemGridConstants.gridColumnOrder.DESC
        );
        expect(orderService.getColumnOrder(grid.header.columns[0])).toBe(
            zemGridConstants.gridColumnOrder.NONE
        );
        expect(orderService.getColumnOrder(grid.header.columns[1])).toBe(
            zemGridConstants.gridColumnOrder.NONE
        );
        expect(orderService.getColumnOrder(grid.header.columns[2])).toBe(
            zemGridConstants.gridColumnOrder.DESC
        );
    });

    it('should pass order to data service', function() {
        var grid = createGrid();
        var pubsub = grid.meta.pubsub;
        spyOn(grid.meta.dataService, 'setOrder');

        var orderService = zemGridOrderService.createInstance(grid);
        pubsub.notify(pubsub.EVENTS.METADATA_UPDATED);

        orderService.setColumnOrder(
            grid.header.columns[1],
            zemGridConstants.gridColumnOrder.ASC
        );
        expect(grid.meta.dataService.setOrder).toHaveBeenCalledWith(
            'field2',
            jasmine.any(Boolean)
        );

        orderService.setColumnOrder(
            grid.header.columns[1],
            zemGridConstants.gridColumnOrder.DESC
        );
        expect(grid.meta.dataService.setOrder).toHaveBeenCalledWith(
            '-field2',
            jasmine.any(Boolean)
        );

        orderService.setColumnOrder(
            grid.header.columns[2],
            zemGridConstants.gridColumnOrder.ASC
        );
        expect(grid.meta.dataService.setOrder).toHaveBeenCalledWith(
            'orderField3',
            jasmine.any(Boolean)
        );

        orderService.setColumnOrder(
            grid.header.columns[2],
            zemGridConstants.gridColumnOrder.DESC
        );
        expect(grid.meta.dataService.setOrder).toHaveBeenCalledWith(
            '-orderField3',
            jasmine.any(Boolean)
        );
    });
});
