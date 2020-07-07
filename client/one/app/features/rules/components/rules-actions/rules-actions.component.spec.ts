import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {RulesActionsComponent} from './rules-actions.component';

describe('DealsActionsComponent', () => {
    let component: RulesActionsComponent;
    let fixture: ComponentFixture<RulesActionsComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [RulesActionsComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(RulesActionsComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
