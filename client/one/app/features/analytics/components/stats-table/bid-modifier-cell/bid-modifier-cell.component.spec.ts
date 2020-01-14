import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {BidModifierCellComponent} from './bid-modifier-cell.component';
import {BidRangeInfoComponent} from '../bid-range-info/bid-range-info.component';
import {EditableCellComponent} from '../editable-cell/editable-cell.component';
import {SharedModule} from '../../../../../shared/shared.module';
import {CoreModule} from '../../../../../core/core.module';

describe('BidModifierCellComponent', () => {
    let component: BidModifierCellComponent;
    let fixture: ComponentFixture<BidModifierCellComponent>;
    let ajs$rootScopeStub: any;

    beforeEach(() => {
        ajs$rootScopeStub = {
            $on: () => {},
        };
        TestBed.configureTestingModule({
            declarations: [
                EditableCellComponent,
                BidRangeInfoComponent,
                BidModifierCellComponent,
            ],
            imports: [FormsModule, SharedModule, CoreModule],
            providers: [
                {
                    provide: 'ajs$rootScope',
                    useValue: ajs$rootScopeStub,
                },
            ],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(BidModifierCellComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
