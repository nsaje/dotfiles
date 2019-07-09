import {
    Currency,
    CampaignType,
    CampaignGoalKPI,
    Unit,
    DataType,
} from '../../../app.constants';
import {APP_CONFIG} from '../../../app.config';
import * as campaignGoalsHelpers from './campaign-goals.helpers';
import {CAMPAIGN_GOAL_KPIS} from '../entity-manager.config';
import {CampaignGoal} from '../../../core/entities/types/campaign/campaign-goal';
import {CampaignGoalKPIConfig} from '../types/campaign-goal-kpi-config';

describe('campaignGoalsHelpers.findCampaignGoalConfig', () => {
    it('should return empty campaign goal config if correct campaign goal config was not found', () => {
        expect(
            campaignGoalsHelpers.findCampaignGoalConfig(
                {
                    id: null,
                    type: null,
                    value: null,
                    primary: false,
                    conversionGoal: null,
                },
                []
            )
        ).toEqual({name: null, value: null, dataType: null});
    });

    it('should find campaign goal config in available campaign goal configs', () => {
        const campaignGoalConfigs: CampaignGoalKPIConfig[] = [
            {
                name: 'Time on Site - Seconds',
                value: CampaignGoalKPI.TIME_ON_SITE,
                dataType: DataType.Decimal,
                unit: Unit.Second,
            },
            {
                name: 'Max Bounce Rate',
                value: CampaignGoalKPI.MAX_BOUNCE_RATE,
                dataType: DataType.Decimal,
                unit: Unit.Percent,
            },
            {
                name: 'Pageviews per Visit',
                value: CampaignGoalKPI.PAGES_PER_SESSION,
                dataType: DataType.Decimal,
            },
        ];
        expect(
            campaignGoalsHelpers.findCampaignGoalConfig(
                {
                    id: null,
                    type: CampaignGoalKPI.MAX_BOUNCE_RATE,
                    value: null,
                    primary: false,
                    conversionGoal: null,
                },
                campaignGoalConfigs
            )
        ).toEqual({
            name: 'Max Bounce Rate',
            value: CampaignGoalKPI.MAX_BOUNCE_RATE,
            dataType: DataType.Decimal,
            unit: Unit.Percent,
        });
    });
});

describe('campaignGoalsHelpers.extendAvailableGoalsWithEditedGoal', () => {
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
                dataType: DataType.Decimal,
                unit: Unit.Second,
            },
            {
                name: 'Max Bounce Rate',
                value: CampaignGoalKPI.MAX_BOUNCE_RATE,
                dataType: DataType.Decimal,
                unit: Unit.Percent,
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
                dataType: DataType.Decimal,
                unit: Unit.Second,
            },
            {
                name: 'Max Bounce Rate',
                value: CampaignGoalKPI.MAX_BOUNCE_RATE,
                dataType: DataType.Decimal,
                unit: Unit.Percent,
            },
            {
                name: 'Pageviews per Visit',
                value: CampaignGoalKPI.PAGES_PER_SESSION,
                dataType: DataType.Decimal,
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
                dataType: DataType.Decimal,
                unit: Unit.Second,
            },
            {
                name: 'Max Bounce Rate',
                value: CampaignGoalKPI.MAX_BOUNCE_RATE,
                dataType: DataType.Decimal,
                unit: Unit.Percent,
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
                dataType: DataType.Decimal,
                unit: Unit.Second,
            },
            {
                name: 'Max Bounce Rate',
                value: CampaignGoalKPI.MAX_BOUNCE_RATE,
                dataType: DataType.Decimal,
                unit: Unit.Percent,
            },
        ]);
    });
});

describe('campaignGoalsHelpers.getAvailableGoals', () => {
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
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
            },
            {
                name: 'CPC',
                value: CampaignGoalKPI.CPC,
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
            },
            {
                name: 'New Users',
                value: CampaignGoalKPI.NEW_UNIQUE_VISITORS,
                dataType: DataType.Decimal,
                unit: Unit.Percent,
            },
            {
                name: 'CPA - Setup Conversion Tracking',
                value: CampaignGoalKPI.CPA,
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
            },
            {
                name: 'Cost per Non-Bounced Visit',
                value: CampaignGoalKPI.CP_NON_BOUNCED_VISIT,
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
            },
            {
                name: 'Cost per New Visitor',
                value: CampaignGoalKPI.CP_NEW_VISITOR,
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
            },
            {
                name: 'Cost per Pageview',
                value: CampaignGoalKPI.CP_PAGE_VIEW,
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
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
                dataType: DataType.Currency,
                unit: Unit.CurrencySign,
            },
        ]);
    });
});

describe('campaignGoalsHelpers.getCampaignGoalDescription', () => {
    it('should return empty description if no campaign goal provided', () => {
        expect(
            campaignGoalsHelpers.getCampaignGoalDescription(null, null)
        ).toEqual('');
    });

    it('should return correct description for decimal goal value with percent unit', () => {
        expect(
            campaignGoalsHelpers.getCampaignGoalDescription(
                {
                    id: null,
                    type: CampaignGoalKPI.MAX_BOUNCE_RATE,
                    value: '50',
                    primary: false,
                    conversionGoal: null,
                },
                null
            )
        ).toEqual('50.00% Bounce Rate');
    });

    it('should return correct description for decimal goal value with unit different than percent', () => {
        expect(
            campaignGoalsHelpers.getCampaignGoalDescription(
                {
                    id: null,
                    type: CampaignGoalKPI.TIME_ON_SITE,
                    value: '10',
                    primary: false,
                    conversionGoal: null,
                },
                null
            )
        ).toEqual('10.00 seconds Time on Site');
    });

    it('should return correct description for currency goal value', () => {
        expect(
            campaignGoalsHelpers.getCampaignGoalDescription(
                {
                    id: null,
                    type: CampaignGoalKPI.CP_NEW_VISITOR,
                    value: '1.234',
                    primary: false,
                    conversionGoal: null,
                },
                Currency.EUR
            )
        ).toEqual('€1.23 Cost per New Visitor');
    });

    it('should return correct description for CPC goal value', () => {
        expect(
            campaignGoalsHelpers.getCampaignGoalDescription(
                {
                    id: null,
                    type: CampaignGoalKPI.CPC,
                    value: '1.234',
                    primary: false,
                    conversionGoal: null,
                },
                Currency.EUR
            )
        ).toEqual('€1.234 CPC');
    });
});
