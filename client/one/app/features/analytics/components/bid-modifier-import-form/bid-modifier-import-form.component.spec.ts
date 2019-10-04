import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {CoreModule} from '../../../../core/core.module';
import {BidModifierImportFormComponent} from './bid-modifier-import-form.component';

describe('BidModifierImportFormComponent', () => {
    let component: BidModifierImportFormComponent;
    let fixture: ComponentFixture<BidModifierImportFormComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [BidModifierImportFormComponent],
            imports: [FormsModule, SharedModule, CoreModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(BidModifierImportFormComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
