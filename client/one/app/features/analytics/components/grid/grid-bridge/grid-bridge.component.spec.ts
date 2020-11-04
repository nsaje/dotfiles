import {ComponentFixture, TestBed} from '@angular/core/testing';
import {RouterTestingModule} from '@angular/router/testing';
import {NotificationService} from '../../../../../core/notification/services/notification.service';
import {SharedModule} from '../../../../../shared/shared.module';
import {GridBridgeComponent} from './grid-bridge.component';
import {GridBridgeStore} from './services/grid-bridge.store';
import {Grid} from './types/grid';
import {GridMeta} from './types/grid-meta';

describe('GridBridgeComponent', () => {
    let component: GridBridgeComponent;
    let fixture: ComponentFixture<GridBridgeComponent>;
    let mockedGrid: Grid;

    beforeEach(() => {
        mockedGrid = {
            header: null,
            body: null,
            footer: null,
            meta: null,
        };
        (mockedGrid.meta as Partial<GridMeta>) = {
            api: {
                onSelectionUpdated: () => {},
                onDataUpdatedError: () => {},
                onRowDataUpdatedError: () => {},
            },
        };

        TestBed.configureTestingModule({
            declarations: [GridBridgeComponent],
            imports: [SharedModule, RouterTestingModule.withRoutes([])],
            providers: [
                {
                    provide: GridBridgeStore,
                    useValue: GridBridgeStore,
                },
                {
                    provide: NotificationService,
                    useValue: {
                        error: () => {},
                    },
                },
            ],
        }).compileComponents();
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(GridBridgeComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();

        spyOn(component.store, 'initStore')
            .and.callThrough()
            .calls.reset();
        spyOn(component.store, 'connect')
            .and.callFake(() => {})
            .calls.reset();

        component.grid = mockedGrid;
        component.ngOnInit();

        expect(component.store.initStore).toHaveBeenCalledWith(mockedGrid);
        expect(component.store.initStore).toHaveBeenCalledTimes(1);
        expect(component.store.connect).toHaveBeenCalledTimes(1);
    });
});
