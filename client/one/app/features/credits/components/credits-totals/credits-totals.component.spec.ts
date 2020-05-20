import {TestBed, ComponentFixture} from '@angular/core/testing';
import {SharedModule} from '../../../../shared/shared.module';
import {CreditsTotalsComponent} from './credits-totals.component';
import {Currency} from '../../../../app.constants';
import {CreditTotal} from '../../../../core/credits/types/credit-total';

describe('CreditsTotalsComponent', () => {
    let component: CreditsTotalsComponent;
    let fixture: ComponentFixture<CreditsTotalsComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CreditsTotalsComponent],
            imports: [SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CreditsTotalsComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should format totals', () => {
        const mockedCreditTotals: CreditTotal[] = [
            {
                total: '1668222.0000',
                allocated: '149862.1593',
                past: '1118222.0000',
                available: '400137.8407',
                currency: Currency.USD,
            },
        ];
        component.creditTotals = mockedCreditTotals;
        component.ngOnChanges();
        expect(component.formattedCreditTotals).toEqual([
            {
                total: '$1,668,222.00',
                allocated: '$149,862.16',
                past: '$1,118,222.00',
                available: '$400,137.84',
            },
        ]);
    });
});
