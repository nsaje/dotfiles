import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../../../../shared/shared.module';
import {BidRangeInfoComponent} from './bid-range-info.component';

describe('BidRangeInfoComponent', () => {
    let component: BidRangeInfoComponent;
    let fixture: ComponentFixture<BidRangeInfoComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [BidRangeInfoComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(BidRangeInfoComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
