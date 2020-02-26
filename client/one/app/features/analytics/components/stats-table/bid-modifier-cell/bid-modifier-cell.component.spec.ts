import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {BidModifierCellComponent} from './bid-modifier-cell.component';
import {BidRangeInfoComponent} from '../bid-range-info/bid-range-info.component';
import {EditableCellComponent} from '../editable-cell/editable-cell.component';
import {SharedModule} from '../../../../../shared/shared.module';
import {CoreModule} from '../../../../../core/core.module';
import {RouterTestingModule} from '@angular/router/testing';

describe('BidModifierCellComponent', () => {
    let component: BidModifierCellComponent;
    let fixture: ComponentFixture<BidModifierCellComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                EditableCellComponent,
                BidRangeInfoComponent,
                BidModifierCellComponent,
            ],
            imports: [
                FormsModule,
                SharedModule,
                CoreModule,
                RouterTestingModule.withRoutes([]),
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
