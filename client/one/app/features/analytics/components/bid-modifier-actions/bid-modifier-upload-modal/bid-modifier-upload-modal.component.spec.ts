import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../../shared/shared.module';
import {CoreModule} from '../../../../../core/core.module';
import {BidModifierUploadModalComponent} from './bid-modifier-upload-modal.component';

describe('BidModifierUploadModalComponent', () => {
    let component: BidModifierUploadModalComponent;
    let fixture: ComponentFixture<BidModifierUploadModalComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [BidModifierUploadModalComponent],
            imports: [FormsModule, SharedModule, CoreModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(BidModifierUploadModalComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
