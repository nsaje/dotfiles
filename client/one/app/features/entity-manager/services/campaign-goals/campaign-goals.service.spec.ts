import {CampaignGoalsService} from './campaign-goals.service';
import {APP_CONSTANTS, Currency, CampaignType} from '../../../../app.constants';
import {APP_CONFIG} from '../../../../app.config';

describe('CampaignGoalsService', () => {
    let service: CampaignGoalsService;
    let multicurrencyServiceSpy: any;
    let zemNavigationNewService: any;

    beforeEach(() => {
        multicurrencyServiceSpy = jasmine.createSpyObj('MulticurrencyService', [
            'getAppropriateCurrencySymbol',
        ]);
        zemNavigationNewService = jasmine.createSpyObj(
            'zemNavigationNewService',
            ['getActiveAccount']
        );
        multicurrencyServiceSpy.getAppropriateCurrencySymbol.and.returnValue(
            APP_CONFIG.currencySymbols[Currency.USD]
        );
        service = new CampaignGoalsService(
            multicurrencyServiceSpy,
            zemNavigationNewService
        );
    });

    it('should correctly filter available goals for display campaign', () => {
        const availableGoals = service.getAvailableGoals(
            [
                {
                    type: APP_CONSTANTS.campaignGoalKPI.TIME_ON_SITE,
                },
                {
                    type: APP_CONSTANTS.campaignGoalKPI.MAX_BOUNCE_RATE,
                },
                {
                    type: APP_CONSTANTS.campaignGoalKPI.PAGES_PER_SESSION,
                },
            ],
            CampaignType.DISPLAY,
            false
        );

        expect(availableGoals).toEqual([
            {
                name: 'Cost per Visit',
                value: APP_CONSTANTS.campaignGoalKPI.CPV,
                unit: APP_CONFIG.currencySymbols[Currency.USD],
            },
            {
                name: 'CPC',
                value: APP_CONSTANTS.campaignGoalKPI.CPC,
                unit: APP_CONFIG.currencySymbols[Currency.USD],
            },
            {
                name: 'New Users',
                value: APP_CONSTANTS.campaignGoalKPI.NEW_UNIQUE_VISITORS,
                unit: '%',
            },
            {
                name: 'CPA - Setup Conversion Tracking',
                value: APP_CONSTANTS.campaignGoalKPI.CPA,
                unit: APP_CONFIG.currencySymbols[Currency.USD],
            },
            {
                name: 'Cost per Non-Bounced Visit',
                value: APP_CONSTANTS.campaignGoalKPI.CP_NON_BOUNCED_VISIT,
                unit: APP_CONFIG.currencySymbols[Currency.USD],
            },
            {
                name: 'Cost per New Visitor',
                value: APP_CONSTANTS.campaignGoalKPI.CP_NEW_VISITOR,
                unit: APP_CONFIG.currencySymbols[Currency.USD],
            },
            {
                name: 'Cost per Pageview',
                value: APP_CONSTANTS.campaignGoalKPI.CP_PAGE_VIEW,
                unit: APP_CONFIG.currencySymbols[Currency.USD],
            },
        ]);
    });

    it('should correctly filter available goals (onlyCpc)', () => {
        const availableGoals = service.getAvailableGoals(
            [],
            CampaignType.DISPLAY,
            true
        );

        expect(availableGoals).toEqual([
            {
                name: 'CPC',
                value: APP_CONSTANTS.campaignGoalKPI.CPC,
                unit: APP_CONFIG.currencySymbols[Currency.USD],
            },
        ]);
    });
});
