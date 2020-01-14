import {SimpleChange} from '@angular/core';
import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {BidModifiersOverviewComponent} from './bid-modifiers-overview.component';
import {BidModifierType} from '../../../../../app/app.constants';
import {BidModifierTypeSummary} from '../../../../core/bid-modifiers/types/bid-modifier-type-summary';

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

    it('should correctly generate grid row data', () => {
        const bidModifierTypeSummaries: BidModifierTypeSummary[] = [
            {type: BidModifierType.DEVICE, count: 1, min: 1.05, max: 0.98},
        ];
        (component.bidModifierTypeSummaries = bidModifierTypeSummaries),
            component.ngOnChanges();
        expect(component.gridRowData).toEqual([
            {
                type: BidModifierType.DEVICE,
                count: 1,
                limits: {
                    min: 1.05,
                    max: 0.98,
                },
            },
        ]);
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
