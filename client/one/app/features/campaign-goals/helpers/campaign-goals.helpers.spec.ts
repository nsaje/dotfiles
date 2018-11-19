import {APP_CONSTANTS, CURRENCY_SYMBOL, CURRENCY} from '../../../app.constants';
import {APP_OPTIONS} from '../../../app.options';
import * as campaignGoalsHelpers from './campaign-goals.helpers';

describe('CampaignGoalsHelpers', () => {
    it('should correctly extend available goals with edited campaign goal', () => {
        const editedCampaignGoal = {
            type: APP_CONSTANTS.campaignGoalKPI.PAGES_PER_SESSION,
        };

        const availableGoals: any[] = [
            {
                name: 'Time on Site - Seconds',
                value: APP_CONSTANTS.campaignGoalKPI.TIME_ON_SITE,
                unit: 's',
            },
            {
                name: 'Max Bounce Rate',
                value: APP_CONSTANTS.campaignGoalKPI.MAX_BOUNCE_RATE,
                unit: '%',
            },
        ];

        const newAvailableGoals = campaignGoalsHelpers.extendAvailableGoalsWithEditedGoal(
            editedCampaignGoal,
            availableGoals,
            APP_OPTIONS.campaignGoalKPIs
        );

        expect(newAvailableGoals).toEqual([
            {
                name: 'Time on Site - Seconds',
                value: APP_CONSTANTS.campaignGoalKPI.TIME_ON_SITE,
                unit: 's',
            },
            {
                name: 'Max Bounce Rate',
                value: APP_CONSTANTS.campaignGoalKPI.MAX_BOUNCE_RATE,
                unit: '%',
            },
            {
                name: 'Pageviews per Visit',
                value: APP_CONSTANTS.campaignGoalKPI.PAGES_PER_SESSION,
            },
        ]);
    });

    it('should not extend available goals with existing edited campaign goal', () => {
        const editedCampaignGoal = {
            type: APP_CONSTANTS.campaignGoalKPI.TIME_ON_SITE,
        };

        const availableGoals: any[] = [
            {
                name: 'Time on Site - Seconds',
                value: APP_CONSTANTS.campaignGoalKPI.TIME_ON_SITE,
                unit: 's',
            },
            {
                name: 'Max Bounce Rate',
                value: APP_CONSTANTS.campaignGoalKPI.MAX_BOUNCE_RATE,
                unit: '%',
            },
        ];

        const newAvailableGoals = campaignGoalsHelpers.extendAvailableGoalsWithEditedGoal(
            editedCampaignGoal,
            availableGoals,
            APP_OPTIONS.campaignGoalKPIs
        );

        expect(newAvailableGoals).toEqual([
            {
                name: 'Time on Site - Seconds',
                value: APP_CONSTANTS.campaignGoalKPI.TIME_ON_SITE,
                unit: 's',
            },
            {
                name: 'Max Bounce Rate',
                value: APP_CONSTANTS.campaignGoalKPI.MAX_BOUNCE_RATE,
                unit: '%',
            },
        ]);
    });

    it('should correctly filter available goals for display campaign', () => {
        const availableGoals = campaignGoalsHelpers.getAvailableGoals(
            APP_OPTIONS.campaignGoalKPIs,
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
            APP_CONSTANTS.campaignTypes.DISPLAY,
            false
        );

        expect(availableGoals).toEqual([
            {
                name: 'Cost per Visit',
                value: APP_CONSTANTS.campaignGoalKPI.CPV,
                unit: '__CURRENCY__',
            },
            {
                name: 'CPC',
                value: APP_CONSTANTS.campaignGoalKPI.CPC,
                unit: '__CURRENCY__',
            },
            {
                name: 'New Users',
                value: APP_CONSTANTS.campaignGoalKPI.NEW_UNIQUE_VISITORS,
                unit: '%',
            },
            {
                name: 'CPA - Setup Conversion Tracking',
                value: APP_CONSTANTS.campaignGoalKPI.CPA,
                unit: '__CURRENCY__',
            },
            {
                name: 'Cost per Non-Bounced Visit',
                value: APP_CONSTANTS.campaignGoalKPI.CP_NON_BOUNCED_VISIT,
                unit: '__CURRENCY__',
            },
            {
                name: 'Cost per New Visitor',
                value: APP_CONSTANTS.campaignGoalKPI.CP_NEW_VISITOR,
                unit: '__CURRENCY__',
            },
            {
                name: 'Cost per Pageview',
                value: APP_CONSTANTS.campaignGoalKPI.CP_PAGE_VIEW,
                unit: '__CURRENCY__',
            },
        ]);
    });

    it('should correctly filter available goals (onlyCpc)', () => {
        const availableGoals = campaignGoalsHelpers.getAvailableGoals(
            APP_OPTIONS.campaignGoalKPIs,
            [],
            APP_CONSTANTS.campaignTypes.CONTENT,
            true
        );

        expect(availableGoals).toEqual([
            {
                name: 'CPC',
                value: APP_CONSTANTS.campaignGoalKPI.CPC,
                unit: '__CURRENCY__',
            },
        ]);
    });

    it('should correctly map available goals to currency symbol', () => {
        const availableGoals = [
            {
                name: 'Cost per Visit',
                value: APP_CONSTANTS.campaignGoalKPI.CPV,
                unit: '__CURRENCY__',
            },
            {
                name: 'CPC',
                value: APP_CONSTANTS.campaignGoalKPI.CPC,
                unit: '__CURRENCY__',
            },
            {
                name: 'New Users',
                value: APP_CONSTANTS.campaignGoalKPI.NEW_UNIQUE_VISITORS,
                unit: '%',
            },
        ];

        const newAvailableGoals = campaignGoalsHelpers.mapAvailableGoalsToCurrencySymbol(
            availableGoals,
            CURRENCY_SYMBOL[CURRENCY.USD]
        );

        expect(newAvailableGoals).toEqual([
            {
                name: 'Cost per Visit',
                value: APP_CONSTANTS.campaignGoalKPI.CPV,
                unit: CURRENCY_SYMBOL[CURRENCY.USD],
            },
            {
                name: 'CPC',
                value: APP_CONSTANTS.campaignGoalKPI.CPC,
                unit: CURRENCY_SYMBOL[CURRENCY.USD],
            },
            {
                name: 'New Users',
                value: APP_CONSTANTS.campaignGoalKPI.NEW_UNIQUE_VISITORS,
                unit: '%',
            },
        ]);
    });
});
