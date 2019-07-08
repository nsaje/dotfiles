import {CampaignSettingsStore} from './campaign-settings.store';
import {CampaignService} from '../../../../core/entities/services/campaign/campaign.service';
import {CampaignWithExtras} from '../../../../core/entities/types/campaign/campaign-with-extras';
import {Campaign} from '../../../../core/entities/types/campaign/campaign';
import {CampaignExtras} from '../../../../core/entities/types/campaign/campaign-extras';
import * as clone from 'clone';
import {CampaignGoal} from '../../../../core/entities/types/campaign/campaign-goal';
import {CampaignGoalKPI} from '../../../../app.constants';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {of} from 'rxjs';
import {ConversionPixelsService} from '../../../../core/conversion-pixels/services/conversion-pixels.service';

describe('CampaignSettingsStore', () => {
    let campaignServiceStub: jasmine.SpyObj<CampaignService>;
    let conversionPixelsServiceStub: jasmine.SpyObj<ConversionPixelsService>;
    let store: CampaignSettingsStore;
    let campaignWithExtras: CampaignWithExtras;
    let campaign: Campaign;
    let campaignExtras: CampaignExtras;

    beforeEach(() => {
        campaignServiceStub = jasmine.createSpyObj(CampaignService.name, [
            'defaults',
            'get',
            'validate',
            'save',
            'archive',
        ]);
        conversionPixelsServiceStub = jasmine.createSpyObj(
            ConversionPixelsService.name,
            ['list', 'save']
        );

        store = new CampaignSettingsStore(
            campaignServiceStub,
            conversionPixelsServiceStub
        );
        campaign = clone(store.state.entity);
        campaignExtras = clone(store.state.extras);
        campaignWithExtras = {
            campaign: campaign,
            extras: campaignExtras,
        };
    });

    it('should correctly create goal', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue(of())
            .calls.reset();

        const goals: CampaignGoal[] = [
            {
                id: '1',
                type: CampaignGoalKPI.CP_NEW_VISITOR,
                value: '12.00',
                primary: true,
                conversionGoal: null,
            },
            {
                id: '2',
                type: CampaignGoalKPI.CP_PAGE_VIEW,
                value: '44.00',
                primary: false,
                conversionGoal: null,
            },
        ];
        store.updateState(goals, 'entity', 'goals');
        expect(store.state.entity.goals).toEqual(goals);
        store.createGoal();
        const newGoals: CampaignGoal[] = [
            {
                id: '1',
                type: CampaignGoalKPI.CP_NEW_VISITOR,
                value: '12.00',
                primary: false,
                conversionGoal: null,
            },
            {
                id: '2',
                type: CampaignGoalKPI.CP_PAGE_VIEW,
                value: '44.00',
                primary: false,
                conversionGoal: null,
            },
            {
                id: null,
                type: null,
                value: null,
                primary: true,
                conversionGoal: null,
            },
        ];
        expect(store.state.entity.goals).toEqual(newGoals);
    });

    it('should correctly set primary goal', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue(of())
            .calls.reset();

        const goals: CampaignGoal[] = [
            {
                id: '1',
                type: CampaignGoalKPI.CP_NEW_VISITOR,
                value: '12.00',
                primary: true,
                conversionGoal: null,
            },
            {
                id: '2',
                type: CampaignGoalKPI.CP_PAGE_VIEW,
                value: '44.00',
                primary: false,
                conversionGoal: null,
            },
        ];
        store.updateState(goals, 'entity', 'goals');
        expect(store.state.entity.goals).toEqual(goals);
        expect(store.state.entity.goals[0].primary).toEqual(true);
        expect(store.state.entity.goals[1].primary).toEqual(false);
        store.setPrimaryGoal(goals[1]);
        expect(store.state.entity.goals[0].primary).toEqual(false);
        expect(store.state.entity.goals[1].primary).toEqual(true);
    });

    it('should correctly change goal', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue(of())
            .calls.reset();

        const goals: CampaignGoal[] = [
            {
                id: '1',
                type: CampaignGoalKPI.CP_NEW_VISITOR,
                value: '12.00',
                primary: true,
                conversionGoal: null,
            },
            {
                id: '2',
                type: CampaignGoalKPI.CP_PAGE_VIEW,
                value: '44.00',
                primary: false,
                conversionGoal: null,
            },
        ];
        store.updateState(goals, 'entity', 'goals');
        expect(store.state.entity.goals).toEqual(goals);

        const changeEvent: ChangeEvent<CampaignGoal> = {
            target: goals[1],
            changes: {
                value: '99.00',
            },
        };

        store.changeGoal(changeEvent);
        expect(store.state.entity.goals[1].value).toEqual('99.00');
    });

    it('should correctly delete goal', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue(of())
            .calls.reset();

        const goals: CampaignGoal[] = [
            {
                id: '1',
                type: CampaignGoalKPI.CP_NEW_VISITOR,
                value: '12.00',
                primary: true,
                conversionGoal: null,
            },
            {
                id: '2',
                type: CampaignGoalKPI.CP_PAGE_VIEW,
                value: '44.00',
                primary: false,
                conversionGoal: null,
            },
        ];
        store.updateState(goals, 'entity', 'goals');
        expect(store.state.entity.goals).toEqual(goals);

        store.deleteGoal(goals[0]);
        expect(store.state.entity.goals).toEqual([
            {
                id: '2',
                type: CampaignGoalKPI.CP_PAGE_VIEW,
                value: '44.00',
                primary: true,
                conversionGoal: null,
            },
        ]);
    });
});
