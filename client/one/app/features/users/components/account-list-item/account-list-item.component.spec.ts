import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {AccountListItemComponent} from './account-list-item.component';

describe('AccountListItemComponent', () => {
    let component: AccountListItemComponent;
    let fixture: ComponentFixture<AccountListItemComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [AccountListItemComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(AccountListItemComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
