import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {CampaignBudgetEditFormComponent} from './campaign-budget-edit-form.component';
import {Currency, CreditStatus} from '../../../../app.constants';
import {SimpleChange} from '@angular/core';
import {Credit} from '../../../../core/credits/types/credit';
import {CampaignBudget} from '../../../../core/entities/types/campaign/campaign-budget';
import {APP_CONFIG} from '../../../../app.config';

describe('CampaignBudgetEditFormComponent', () => {
    let component: CampaignBudgetEditFormComponent;
    let fixture: ComponentFixture<CampaignBudgetEditFormComponent>;
    const mockedBudget: CampaignBudget = {
        id: '123',
        creditId: '100',
        startDate: new Date(1970, 2, 23),
        endDate: new Date(1970, 3, 10),
        amount: '1000000',
        margin: '15.00',
        licenseFee: '13.05',
        comment: 'A generic comment',
        canEditStartDate: true,
        canEditEndDate: false,
        canEditAmount: true,
    };
    const mockedCredits: Credit[] = [
        {
            id: '100',
            createdOn: new Date(1970, 1, 21),
            status: CreditStatus.SIGNED,
            agencyId: '123',
            accountId: null,
            startDate: new Date(1970, 2, 21),
            endDate: new Date(1970, 3, 21),
            licenseFee: '13.05',
            amount: 5000000,
            total: '5000000',
            allocated: '3000000',
            available: '2000000',
            currency: Currency.USD,
            contractId: null,
            contractNumber: null,
            comment: 'A generic credit',
            salesforceUrl: null,
            isAvailable: true,
        },
    ];

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CampaignBudgetEditFormComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CampaignBudgetEditFormComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it("should correctly format credits' data on change", () => {
        component.budget = mockedBudget;
        component.currency = Currency.EUR;
        component.credits = mockedCredits;
        component.ngOnChanges({
            credits: new SimpleChange(null, mockedCredits, false),
        });
        expect(component.currencySymbol).toEqual(
            APP_CONFIG.currencySymbols[Currency.EUR]
        );
        expect(component.formattedCredits).toEqual([
            {
                ...mockedCredits[0],
                createdOn: '02/21/1970',
                startDate: '03/21/1970',
                endDate: '04/21/1970',
                total: '€5,000,000.00',
                allocated: '€3,000,000.00',
                available: '€2,000,000.00',
                licenseFee: '13.05%',
            },
        ]);
    });

    it("should correctly format credits' data on currency change", () => {
        component.budget = mockedBudget;
        component.currency = Currency.USD;
        component.credits = mockedCredits;
        component.ngOnChanges({
            currency: new SimpleChange(null, Currency.USD, false),
        });
        expect(component.currencySymbol).toEqual(
            APP_CONFIG.currencySymbols[Currency.USD]
        );
        expect(component.formattedCredits).toEqual([
            {
                ...mockedCredits[0],
                createdOn: '02/21/1970',
                startDate: '03/21/1970',
                endDate: '04/21/1970',
                total: '$5,000,000.00',
                allocated: '$3,000,000.00',
                available: '$2,000,000.00',
                licenseFee: '13.05%',
            },
        ]);
    });
});
