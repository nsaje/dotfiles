import {TestBed, ComponentFixture} from '@angular/core/testing';
import {RulesHistoriesGridComponent} from './rules-histories-grid.component';
import {SharedModule} from '../../../../shared/shared.module';

describe('RulesHistoriesGridComponent', () => {
    let component: RulesHistoriesGridComponent;
    let fixture: ComponentFixture<RulesHistoriesGridComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [RulesHistoriesGridComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(RulesHistoriesGridComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
