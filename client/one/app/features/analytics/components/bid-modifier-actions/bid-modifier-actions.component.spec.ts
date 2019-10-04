import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {BidModifierActionsComponent} from './bid-modifier-actions.component';
import {BidModifierImportFormComponent} from '../bid-modifier-import-form/bid-modifier-import-form.component';

describe('BidModifierActionsComponent', () => {
    let component: BidModifierActionsComponent;
    let fixture: ComponentFixture<BidModifierActionsComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                BidModifierActionsComponent,
                BidModifierImportFormComponent,
            ],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(BidModifierActionsComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
