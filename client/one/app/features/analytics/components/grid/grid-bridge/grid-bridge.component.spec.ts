import {ComponentFixture, TestBed} from '@angular/core/testing';
import {SharedModule} from '../../../../../shared/shared.module';
import {GridBridgeComponent} from './grid-bridge.component';
import {GridBridgeStore} from './services/grid-bridge.store';
import {Grid} from './types/grid';

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

        TestBed.configureTestingModule({
            declarations: [GridBridgeComponent],
            imports: [SharedModule],
            providers: [
                {
                    provide: GridBridgeStore,
                    useValue: GridBridgeStore,
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
