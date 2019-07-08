import {Currency, CampaignType, CampaignGoalKPI} from '../../../app.constants';
import {APP_CONFIG} from '../../../app.config';
import * as campaignGoalsHelpers from './campaign-goals.helpers';
import {CAMPAIGN_GOAL_KPIS} from '../entity-manager.config';
import {CampaignGoal} from '../../../core/entities/types/campaign/campaign-goal';
import {CampaignGoalKPIConfig} from '../types/campaign-goal-kpi-config';

describe('CampaignGoalsHelpers', () => {
    it('should correctly extend available goals with edited campaign goal', () => {
        const editedCampaignGoal: CampaignGoal = {
            id: null,
            type: CampaignGoalKPI.PAGES_PER_SESSION,
            value: null,
            primary: false,
            conversionGoal: null,
        };

        const availableGoals: CampaignGoalKPIConfig[] = [
            {
                name: 'Time on Site - Seconds',
                value: CampaignGoalKPI.TIME_ON_SITE,
                unit: 's',
            },
            {
                name: 'Max Bounce Rate',
                value: CampaignGoalKPI.MAX_BOUNCE_RATE,
                unit: '%',
            },
        ];

        const newAvailableGoals = campaignGoalsHelpers.extendAvailableGoalsWithEditedGoal(
            editedCampaignGoal,
            availableGoals,
            CAMPAIGN_GOAL_KPIS
        );

        expect(newAvailableGoals).toEqual([
            {
                name: 'Time on Site - Seconds',
                value: CampaignGoalKPI.TIME_ON_SITE,
                unit: 's',
            },
            {
                name: 'Max Bounce Rate',
                value: CampaignGoalKPI.MAX_BOUNCE_RATE,
                unit: '%',
            },
            {
                name: 'Pageviews per Visit',
                value: CampaignGoalKPI.PAGES_PER_SESSION,
            },
        ]);
    });

    it('should not extend available goals with existing edited campaign goal', () => {
        const editedCampaignGoal: CampaignGoal = {
            id: null,
            type: CampaignGoalKPI.TIME_ON_SITE,
            value: null,
            primary: false,
            conversionGoal: null,
        };

        const availableGoals: CampaignGoalKPIConfig[] = [
            {
                name: 'Time on Site - Seconds',
                value: CampaignGoalKPI.TIME_ON_SITE,
                unit: 's',
            },
            {
                name: 'Max Bounce Rate',
                value: CampaignGoalKPI.MAX_BOUNCE_RATE,
                unit: '%',
            },
        ];

        const newAvailableGoals = campaignGoalsHelpers.extendAvailableGoalsWithEditedGoal(
            editedCampaignGoal,
            availableGoals,
            CAMPAIGN_GOAL_KPIS
        );

        expect(newAvailableGoals).toEqual([
            {
                name: 'Time on Site - Seconds',
                value: CampaignGoalKPI.TIME_ON_SITE,
                unit: 's',
            },
            {
                name: 'Max Bounce Rate',
                value: CampaignGoalKPI.MAX_BOUNCE_RATE,
                unit: '%',
            },
        ]);
    });

    it('should correctly filter available goals for display campaign', () => {
        const availableGoals = campaignGoalsHelpers.getAvailableGoals(
            CAMPAIGN_GOAL_KPIS,
            [
                {
                    id: null,
                    type: CampaignGoalKPI.TIME_ON_SITE,
                    value: null,
                    primary: false,
                    conversionGoal: null,
                },
                {
                    id: null,
                    type: CampaignGoalKPI.MAX_BOUNCE_RATE,
                    value: null,
                    primary: false,
                    conversionGoal: null,
                },
                {
                    id: null,
                    type: CampaignGoalKPI.PAGES_PER_SESSION,
                    value: null,
                    primary: false,
                    conversionGoal: null,
                },
            ],
            CampaignType.DISPLAY,
            false
        );

        expect(availableGoals).toEqual([
            {
                name: 'Cost per Visit',
                value: CampaignGoalKPI.CPV,
                isCurrency: true,
            },
            {
                name: 'CPC',
                value: CampaignGoalKPI.CPC,
                isCurrency: true,
            },
            {
                name: 'New Users',
                value: CampaignGoalKPI.NEW_UNIQUE_VISITORS,
                unit: '%',
            },
            {
                name: 'CPA - Setup Conversion Tracking',
                value: CampaignGoalKPI.CPA,
                isCurrency: true,
            },
            {
                name: 'Cost per Non-Bounced Visit',
                value: CampaignGoalKPI.CP_NON_BOUNCED_VISIT,
                isCurrency: true,
            },
            {
                name: 'Cost per New Visitor',
                value: CampaignGoalKPI.CP_NEW_VISITOR,
                isCurrency: true,
            },
            {
                name: 'Cost per Pageview',
                value: CampaignGoalKPI.CP_PAGE_VIEW,
                isCurrency: true,
            },
        ]);
    });

    it('should correctly filter available goals (onlyCpc)', () => {
        const availableGoals = campaignGoalsHelpers.getAvailableGoals(
            CAMPAIGN_GOAL_KPIS,
            [],
            CampaignType.CONTENT,
            true
        );

        expect(availableGoals).toEqual([
            {
                name: 'CPC',
                value: CampaignGoalKPI.CPC,
                isCurrency: true,
            },
        ]);
    });

    it('should correctly map available goals to currency symbol', () => {
        const availableGoals = [
            {
                name: 'Cost per Visit',
                value: CampaignGoalKPI.CPV,
                isCurrency: true,
            },
            {
                name: 'CPC',
                value: CampaignGoalKPI.CPC,
                isCurrency: true,
            },
            {
                name: 'New Users',
                value: CampaignGoalKPI.NEW_UNIQUE_VISITORS,
                unit: '%',
            },
        ];

        const newAvailableGoals = campaignGoalsHelpers.mapAvailableGoalsToCurrencySymbol(
            availableGoals,
            APP_CONFIG.currencySymbols[Currency.USD]
        );

        expect(newAvailableGoals).toEqual([
            {
                name: 'Cost per Visit',
                value: CampaignGoalKPI.CPV,
                unit: APP_CONFIG.currencySymbols[Currency.USD],
                isCurrency: true,
            },
            {
                name: 'CPC',
                value: CampaignGoalKPI.CPC,
                unit: APP_CONFIG.currencySymbols[Currency.USD],
                isCurrency: true,
            },
            {
                name: 'New Users',
                value: CampaignGoalKPI.NEW_UNIQUE_VISITORS,
                unit: '%',
            },
        ]);
    });
});
