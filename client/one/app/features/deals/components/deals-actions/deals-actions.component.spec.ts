import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {DealsActionsComponent} from './deals-actions.component';

describe('DealsActionsComponent', () => {
    let component: DealsActionsComponent;
    let fixture: ComponentFixture<DealsActionsComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DealsActionsComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DealsActionsComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
