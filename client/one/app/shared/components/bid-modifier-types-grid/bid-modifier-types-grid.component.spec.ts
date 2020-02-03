import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../shared.module';
import {BidModifierTypesGridComponent} from './bid-modifier-types-grid.component';

describe('BidModifierTypesGridComponent', () => {
    let component: BidModifierTypesGridComponent;
    let fixture: ComponentFixture<BidModifierTypesGridComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(BidModifierTypesGridComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
