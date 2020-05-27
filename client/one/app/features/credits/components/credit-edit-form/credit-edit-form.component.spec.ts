import {TestBed, ComponentFixture} from '@angular/core/testing';
import {CreditEditFormComponent} from './credit-edit-form.component';
import {SharedModule} from '../../../../shared/shared.module';

describe('CreditEditFormComponent', () => {
    let component: CreditEditFormComponent;
    let fixture: ComponentFixture<CreditEditFormComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CreditEditFormComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CreditEditFormComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
