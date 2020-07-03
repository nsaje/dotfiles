import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../shared/shared.module';
import {RulesGridComponent} from './rules-grid.component';

describe('RulesGridComponent', () => {
    let component: RulesGridComponent;
    let fixture: ComponentFixture<RulesGridComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [RulesGridComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(RulesGridComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
