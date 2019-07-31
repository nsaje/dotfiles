import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {CampaignBudgetsListComponent} from './campaign-budgets-list.component';
import {Currency, CampaignBudgetState} from '../../../../app.constants';
import {SimpleChange} from '@angular/core';

describe('CampaignBudgetsListComponent', () => {
    let component: CampaignBudgetsListComponent;
    let fixture: ComponentFixture<CampaignBudgetsListComponent>;
    const mockedBudgets = [
        {
            id: '100',
            creditId: '1',
            state: CampaignBudgetState.ACTIVE,
            startDate: new Date(1970, 1, 21),
            endDate: new Date(1970, 2, 21),
            amount: '5000000',
            available: '2000000',
            spend: '3000000',
            margin: '5000',
            licenseFee: '200',
            comment: 'A generic comment',
            createdDt: new Date(1970, 0, 21),
            createdBy: 'test@test.com',
            canEditStartDate: true,
            canEditEndDate: true,
            canEditAmount: true,
        },
    ];

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CampaignBudgetsListComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CampaignBudgetsListComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it("should correctly format budgets' data on change", () => {
        component.currency = Currency.EUR;
        component.budgets = mockedBudgets;
        component.ngOnChanges({
            budgets: new SimpleChange(null, mockedBudgets, false),
        });
        expect(component.formattedBudgets).toEqual([
            {
                ...mockedBudgets[0],
                startDate: '02/21/1970',
                endDate: '03/21/1970',
                createdDt: '01/21/1970',
                amount: '€5,000,000.00',
                available: '€2,000,000.00',
                spend: '€3,000,000.00',
                margin: '€5,000.00',
                licenseFee: '€200.00',
            },
        ]);
    });

    it("should correctly format budgets' data on currency change", () => {
        component.currency = Currency.USD;
        component.budgets = mockedBudgets;
        component.formattedBudgets = [
            {
                ...mockedBudgets[0],
                startDate: '02/21/1970',
                endDate: '03/21/1970',
                createdDt: '01/21/1970',
                amount: '€5,000,000.00',
                available: '€2,000,000.00',
                spend: '€3,000,000.00',
                margin: '€5,000.00',
                licenseFee: '€200.00',
            },
        ];
        component.ngOnChanges({
            currency: new SimpleChange(null, Currency.USD, false),
        });
        expect(component.formattedBudgets).toEqual([
            {
                ...mockedBudgets[0],
                startDate: '02/21/1970',
                endDate: '03/21/1970',
                createdDt: '01/21/1970',
                amount: '$5,000,000.00',
                available: '$2,000,000.00',
                spend: '$3,000,000.00',
                margin: '$5,000.00',
                licenseFee: '$200.00',
            },
        ]);
    });
});
