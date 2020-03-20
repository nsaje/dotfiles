import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {CreditsScopeSelectorComponent} from './credits-scope-selector.component';

describe('CreditsScopeSelectorComponent', () => {
    let component: CreditsScopeSelectorComponent;
    let fixture: ComponentFixture<CreditsScopeSelectorComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CreditsScopeSelectorComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CreditsScopeSelectorComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
