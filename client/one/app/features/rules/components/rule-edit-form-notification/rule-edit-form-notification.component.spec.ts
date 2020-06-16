import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {RuleEditFormNotificationComponent} from './rule-edit-form-notification.component';

describe('RuleEditFormNotificationComponent', () => {
    let component: RuleEditFormNotificationComponent;
    let fixture: ComponentFixture<RuleEditFormNotificationComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [RuleEditFormNotificationComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(RuleEditFormNotificationComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
