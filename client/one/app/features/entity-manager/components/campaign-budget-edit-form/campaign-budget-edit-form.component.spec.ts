import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {CampaignBudgetEditFormComponent} from './campaign-budget-edit-form.component';
import {Currency, AccountCreditStatus} from '../../../../app.constants';
import {SimpleChange} from '@angular/core';
import {AccountCredit} from '../../../../core/entities/types/account/account-credit';
import {DateSettingComponent} from '../date-setting/date-setting.component';
import {SelectSettingComponent} from '../select-setting/select-setting.component';
import {TextSettingComponent} from '../text-setting/text-setting.component';
import {CurrencySettingComponent} from '../currency-setting/currency-setting.component';
import {TextAreaSettingComponent} from '../textarea-setting/textarea-setting.component';
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
        margin: '200',
        comment: 'A generic comment',
        canEditStartDate: true,
        canEditEndDate: false,
        canEditAmount: true,
    };
    const mockedCredits: AccountCredit[] = [
        {
            id: '100',
            createdOn: new Date(1970, 1, 21),
            startDate: new Date(1970, 2, 21),
            endDate: new Date(1970, 3, 21),
            total: '5000000',
            allocated: '3000000',
            available: '2000000',
            licenseFee: '200',
            status: AccountCreditStatus.SIGNED,
            currency: Currency.USD,
            comment: 'A generic credit',
            isAvailable: true,
            isAgency: true,
        },
    ];

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [
                CampaignBudgetEditFormComponent,
                SelectSettingComponent,
                TextSettingComponent,
                DateSettingComponent,
                CurrencySettingComponent,
                TextAreaSettingComponent,
            ],
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
        component.accountCredits = mockedCredits;
        component.ngOnChanges({
            accountCredits: new SimpleChange(null, mockedCredits, false),
        });
        expect(component.currencySymbol).toEqual(
            APP_CONFIG.currencySymbols[Currency.EUR]
        );
        expect(component.formattedAccountCredits).toEqual([
            {
                ...mockedCredits[0],
                createdOn: '02/21/1970',
                startDate: '03/21/1970',
                endDate: '04/21/1970',
                total: '€5,000,000.00',
                allocated: '€3,000,000.00',
                available: '€2,000,000.00',
                licenseFee: '€200.00',
            },
        ]);
    });

    it("should correctly format credits' data on currency change", () => {
        component.budget = mockedBudget;
        component.currency = Currency.USD;
        component.accountCredits = mockedCredits;
        component.ngOnChanges({
            currency: new SimpleChange(null, Currency.USD, false),
        });
        expect(component.currencySymbol).toEqual(
            APP_CONFIG.currencySymbols[Currency.USD]
        );
        expect(component.formattedAccountCredits).toEqual([
            {
                ...mockedCredits[0],
                createdOn: '02/21/1970',
                startDate: '03/21/1970',
                endDate: '04/21/1970',
                total: '$5,000,000.00',
                allocated: '$3,000,000.00',
                available: '$2,000,000.00',
                licenseFee: '$200.00',
            },
        ]);
    });
});
