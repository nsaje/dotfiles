import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {DealEditFormComponent} from './deal-edit-form.component';

describe('DealEditFormComponent', () => {
    let component: DealEditFormComponent;
    let fixture: ComponentFixture<DealEditFormComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DealEditFormComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DealEditFormComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
