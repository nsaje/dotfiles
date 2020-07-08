import {TestBed, ComponentFixture} from '@angular/core/testing';
import {RulesHistoriesFiltersComponent} from './rules-histories-filters.component';
import {SharedModule} from '../../../../shared/shared.module';

describe('RulesHistoriesFiltersComponent', () => {
    let component: RulesHistoriesFiltersComponent;
    let fixture: ComponentFixture<RulesHistoriesFiltersComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [RulesHistoriesFiltersComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(RulesHistoriesFiltersComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
