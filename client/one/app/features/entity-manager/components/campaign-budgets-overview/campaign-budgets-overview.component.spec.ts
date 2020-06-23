import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {CampaignBudgetsOverviewComponent} from './campaign-budgets-overview.component';
import {SimpleChange} from '@angular/core';
import {Currency} from '../../../../app.constants';

describe('CampaignBudgetsOverviewComponent', () => {
    let component: CampaignBudgetsOverviewComponent;
    let fixture: ComponentFixture<CampaignBudgetsOverviewComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [CampaignBudgetsOverviewComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(CampaignBudgetsOverviewComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly format overview data on change', () => {
        const mockedOverview = {
            campaignSpend: '123.456',
            mediaSpend: '223.456',
            baseMediaSpend: '223.456',
            dataSpend: '323.456',
            baseDataSpend: '323.456',
            licenseFee: '423.456',
            serviceFee: '423.456',
            margin: '523.456',
            availableBudgetsSum: '623.456',
            unallocatedCredit: '723.456',
        };
        component.currency = Currency.EUR;
        component.overview = mockedOverview;
        component.ngOnChanges({
            overview: new SimpleChange(null, mockedOverview, false),
        });
        expect(component.formattedOverview).toEqual({
            campaignSpend: '€123.46',
            mediaSpend: '€223.46',
            baseMediaSpend: '€223.46',
            dataSpend: '€323.46',
            baseDataSpend: '€323.46',
            licenseFee: '€423.46',
            serviceFee: '€423.46',
            margin: '€523.46',
            availableBudgetsSum: '€623.46',
            unallocatedCredit: '€723.46',
        });
    });

    it('should correctly format overview data on currency change', () => {
        component.currency = Currency.USD;
        component.overview = {
            campaignSpend: '123.456',
            mediaSpend: '223.456',
            baseMediaSpend: '223.456',
            dataSpend: '323.456',
            baseDataSpend: '323.456',
            licenseFee: '423.456',
            serviceFee: '423.456',
            margin: '523.456',
            availableBudgetsSum: '623.456',
            unallocatedCredit: '723.456',
        };
        component.formattedOverview = {
            campaignSpend: '€123.46',
            mediaSpend: '€223.46',
            baseMediaSpend: '€223.46',
            dataSpend: '€323.46',
            baseDataSpend: '€323.46',
            licenseFee: '€423.46',
            serviceFee: '€423.46',
            margin: '€523.46',
            availableBudgetsSum: '€623.46',
            unallocatedCredit: '€723.46',
        };
        component.ngOnChanges({
            currency: new SimpleChange(null, Currency.USD, false),
        });
        expect(component.formattedOverview).toEqual({
            campaignSpend: '$123.46',
            mediaSpend: '$223.46',
            baseMediaSpend: '$223.46',
            dataSpend: '$323.46',
            baseDataSpend: '$323.46',
            licenseFee: '$423.46',
            serviceFee: '$423.46',
            margin: '$523.46',
            availableBudgetsSum: '$623.46',
            unallocatedCredit: '$723.46',
        });
    });
});
