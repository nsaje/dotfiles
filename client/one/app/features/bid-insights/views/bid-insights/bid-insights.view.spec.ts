import {TestBed, ComponentFixture} from '@angular/core/testing';
import {RouterTestingModule} from '@angular/router/testing';
import {SharedModule} from '../../../../shared/shared.module';
import {BidInsightsView} from './bid-insights.view';

describe('BidInsightsView', () => {
    let component: BidInsightsView;
    let fixture: ComponentFixture<BidInsightsView>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [BidInsightsView],
            imports: [SharedModule, RouterTestingModule.withRoutes([])],
            providers: [],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(BidInsightsView);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
