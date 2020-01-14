import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {BidModifiersOverviewComponent} from './bid-modifiers-overview.component';

describe('BidModifiersOverviewComponent', () => {
    let component: BidModifiersOverviewComponent;
    let fixture: ComponentFixture<BidModifiersOverviewComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [BidModifiersOverviewComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(BidModifiersOverviewComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly emit import file change event', () => {
        spyOn(component.importFileChange, 'emit').and.stub();

        const bidModifierImportFile = {name: 'upload.csv'} as File;
        component.onFilesChange([bidModifierImportFile]);
        expect(component.importFileChange.emit).toHaveBeenCalledWith(
            bidModifierImportFile
        );
    });
});
