import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {UsersActionsComponent} from './users-actions.component';

describe('UsersActionsComponent', () => {
    let component: UsersActionsComponent;
    let fixture: ComponentFixture<UsersActionsComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [UsersActionsComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(UsersActionsComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
