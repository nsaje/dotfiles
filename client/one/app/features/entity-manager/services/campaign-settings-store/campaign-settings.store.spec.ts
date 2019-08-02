import {CampaignSettingsStore} from './campaign-settings.store';
import {CampaignService} from '../../../../core/entities/services/campaign/campaign.service';
import {CampaignWithExtras} from '../../../../core/entities/types/campaign/campaign-with-extras';
import {Campaign} from '../../../../core/entities/types/campaign/campaign';
import {CampaignExtras} from '../../../../core/entities/types/campaign/campaign-extras';
import * as clone from 'clone';
import {CampaignGoal} from '../../../../core/entities/types/campaign/campaign-goal';
import {
    CampaignGoalKPI,
    CampaignConversionGoalType,
    AccountCreditStatus,
    Currency,
} from '../../../../app.constants';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {of, asapScheduler, throwError} from 'rxjs';
import {ConversionPixelsService} from '../../../../core/conversion-pixels/services/conversion-pixels.service';
import {fakeAsync, tick} from '@angular/core/testing';
import {CampaignSettingsStoreFieldsErrorsState} from './campaign-settings.store.fields-errors-state';
import {ConversionPixel} from '../../../../core/conversion-pixels/types/conversion-pixel';
import {AccountCredit} from '../../../../core/entities/types/account/account-credit';
import * as moment from 'moment';
import {CampaignBudget} from '../../../../core/entities/types/campaign/campaign-budget';

describe('CampaignSettingsStore', () => {
    let campaignServiceStub: jasmine.SpyObj<CampaignService>;
    let conversionPixelsServiceStub: jasmine.SpyObj<ConversionPixelsService>;
    let store: CampaignSettingsStore;
    let campaignWithExtras: CampaignWithExtras;
    let campaign: Campaign;
    let campaignExtras: CampaignExtras;
    let conversionPixels: ConversionPixel[];

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
            ['list', 'create', 'edit']
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

        conversionPixels = [
            {
                id: '123',
                accountId: '12345',
                name: 'Zemanta Pixel 1',
                url: 'http://one.zemanta.com/pixel_1',
                lastTriggered: new Date(),
                impressions: 123,
                conversionWindows: [],
            },
            {
                id: '123',
                accountId: '12345',
                name: 'Zemanta Pixel 2',
                url: 'http://one.zemanta.com/pixel_2',
                lastTriggered: new Date(),
                impressions: 124,
                conversionWindows: [],
            },
        ];
    });

    it('should get default campaign via service', fakeAsync(() => {
        const mockedCampaignWithExtras = clone(campaignWithExtras);
        mockedCampaignWithExtras.campaign.name = 'New campaign';
        mockedCampaignWithExtras.campaign.accountId = '12345';

        campaignServiceStub.defaults.and
            .returnValue(of(mockedCampaignWithExtras, asapScheduler))
            .calls.reset();

        conversionPixelsServiceStub.list.and
            .returnValue(of(clone(conversionPixels)))
            .calls.reset();

        expect(store.state.entity).toEqual(campaign);
        expect(store.state.extras).toEqual(campaignExtras);
        expect(store.state.fieldsErrors).toEqual(
            new CampaignSettingsStoreFieldsErrorsState()
        );
        expect(store.state.conversionPixels).toEqual([]);

        store.loadEntityDefaults('12345');
        tick();

        expect(store.state.entity).toEqual(mockedCampaignWithExtras.campaign);
        expect(store.state.extras).toEqual(mockedCampaignWithExtras.extras);
        expect(store.state.fieldsErrors).toEqual(
            new CampaignSettingsStoreFieldsErrorsState()
        );
        expect(store.state.conversionPixels).toEqual(conversionPixels);

        expect(campaignServiceStub.defaults).toHaveBeenCalledTimes(1);
        expect(conversionPixelsServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should get campaign via service', fakeAsync(() => {
        const mockedCampaignWithExtras = clone(campaignWithExtras);
        mockedCampaignWithExtras.campaign.id = '12345';
        mockedCampaignWithExtras.campaign.name = 'Test campaign 1';
        mockedCampaignWithExtras.campaign.accountId = '12345';

        campaignServiceStub.get.and
            .returnValue(of(mockedCampaignWithExtras, asapScheduler))
            .calls.reset();

        conversionPixelsServiceStub.list.and
            .returnValue(of(clone(conversionPixels)))
            .calls.reset();

        expect(store.state.entity).toEqual(campaign);
        expect(store.state.extras).toEqual(campaignExtras);
        expect(store.state.fieldsErrors).toEqual(
            new CampaignSettingsStoreFieldsErrorsState()
        );
        expect(store.state.conversionPixels).toEqual([]);

        store.loadEntity('12345');
        tick();

        expect(store.state.entity).toEqual(mockedCampaignWithExtras.campaign);
        expect(store.state.extras).toEqual(mockedCampaignWithExtras.extras);
        expect(store.state.fieldsErrors).toEqual(
            new CampaignSettingsStoreFieldsErrorsState()
        );
        expect(store.state.conversionPixels).toEqual(conversionPixels);

        expect(campaignServiceStub.get).toHaveBeenCalledTimes(1);
        expect(conversionPixelsServiceStub.list).toHaveBeenCalledTimes(1);
    }));

    it('should correctly handle errors when validating campaign via service', fakeAsync(() => {
        const mockedCampaignWithExtras = clone(campaignWithExtras);
        mockedCampaignWithExtras.campaign.id = '12345';
        mockedCampaignWithExtras.campaign.accountId = '12345';

        store.state.entity = mockedCampaignWithExtras.campaign;
        store.state.extras = mockedCampaignWithExtras.extras;

        campaignServiceStub.validate.and
            .returnValue(
                throwError({
                    message: 'Validation error',
                    error: {
                        details: {name: ['Please specify campaign name.']},
                    },
                })
            )
            .calls.reset();

        store.validateEntity();
        tick();

        expect(store.state.entity).toEqual(mockedCampaignWithExtras.campaign);
        expect(store.state.extras).toEqual(mockedCampaignWithExtras.extras);
        expect(store.state.fieldsErrors).toEqual(
            jasmine.objectContaining({
                ...new CampaignSettingsStoreFieldsErrorsState(),
                name: ['Please specify campaign name.'],
            })
        );

        expect(campaignServiceStub.validate).toHaveBeenCalledTimes(1);

        campaignServiceStub.validate.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();

        store.validateEntity();
        tick();

        expect(store.state.entity).toEqual(mockedCampaignWithExtras.campaign);
        expect(store.state.extras).toEqual(mockedCampaignWithExtras.extras);
        expect(store.state.fieldsErrors).toEqual(
            new CampaignSettingsStoreFieldsErrorsState()
        );

        expect(campaignServiceStub.validate).toHaveBeenCalledTimes(1);
    }));

    it('should successfully save campaign via service', fakeAsync(() => {
        const mockedCampaignWithExtras = clone(campaignWithExtras);
        mockedCampaignWithExtras.campaign.id = '12345';
        mockedCampaignWithExtras.campaign.name = 'Test campaign 1';
        mockedCampaignWithExtras.campaign.accountId = '12345';
        campaignServiceStub.get.and
            .returnValue(of(mockedCampaignWithExtras, asapScheduler))
            .calls.reset();
        conversionPixelsServiceStub.list.and
            .returnValue(of(clone(conversionPixels)))
            .calls.reset();
        campaignServiceStub.save.and
            .returnValue(of(mockedCampaignWithExtras.campaign, asapScheduler))
            .calls.reset();

        store.loadEntity('12345');
        tick();

        store.saveEntity();
        tick();

        expect(store.state.entity).toEqual(mockedCampaignWithExtras.campaign);
        expect(store.state.fieldsErrors).toEqual(
            new CampaignSettingsStoreFieldsErrorsState()
        );
        expect(campaignServiceStub.save).toHaveBeenCalledTimes(1);
    }));

    it('should correctly handle errors when saving campaign via service', fakeAsync(() => {
        const mockedCampaignWithExtras = clone(campaignWithExtras);
        mockedCampaignWithExtras.campaign.id = '12345';
        mockedCampaignWithExtras.campaign.accountId = '12345';
        campaignServiceStub.get.and
            .returnValue(of(mockedCampaignWithExtras, asapScheduler))
            .calls.reset();
        conversionPixelsServiceStub.list.and
            .returnValue(of(clone(conversionPixels)))
            .calls.reset();
        campaignServiceStub.save.and
            .returnValue(
                throwError({
                    message: 'Validation error',
                    error: {
                        details: {name: ['Please specify campaign name.']},
                    },
                })
            )
            .calls.reset();

        store.loadEntity('12345');
        tick();

        store.saveEntity();
        tick();

        expect(store.state.entity).toEqual(mockedCampaignWithExtras.campaign);
        expect(store.state.fieldsErrors).toEqual(
            jasmine.objectContaining({
                ...new CampaignSettingsStoreFieldsErrorsState(),
                name: ['Please specify campaign name.'],
            })
        );
        expect(campaignServiceStub.save).toHaveBeenCalledTimes(1);
    }));

    it('should successfully archive campaign via service', async () => {
        const mockedCampaign = clone(campaign);
        mockedCampaign.id = '12345';
        mockedCampaign.name = 'Test campaign 1';
        mockedCampaign.accountId = '12345';
        mockedCampaign.archived = false;

        store.state.entity = mockedCampaign;

        const archivedCampaign = clone(mockedCampaign);
        archivedCampaign.archived = true;
        campaignServiceStub.archive.and
            .returnValue(of(archivedCampaign, asapScheduler))
            .calls.reset();

        const shouldReload = await store.archiveEntity();

        expect(campaignServiceStub.archive).toHaveBeenCalledTimes(1);
        expect(shouldReload).toBe(true);
    });

    it('should successfully handle errors when archiving campaign via service', async () => {
        const mockedCampaign = clone(campaign);
        mockedCampaign.id = '12345';
        mockedCampaign.name = 'Test campaign 1';
        mockedCampaign.accountId = '12345';
        mockedCampaign.archived = false;

        store.state.entity = mockedCampaign;

        campaignServiceStub.archive.and
            .returnValue(
                throwError({
                    message: 'Internal server error',
                })
            )
            .calls.reset();

        const shouldReload = await store.archiveEntity();

        expect(campaignServiceStub.archive).toHaveBeenCalledTimes(1);
        expect(shouldReload).toBe(false);
    });

    it('should correctly determine if campaign settings have unsaved changes', fakeAsync(() => {
        campaignServiceStub.get.and
            .returnValue(of(clone(campaignWithExtras), asapScheduler))
            .calls.reset();
        conversionPixelsServiceStub.list.and
            .returnValue(of(clone(conversionPixels)))
            .calls.reset();

        expect(store.doEntitySettingsHaveUnsavedChanges()).toBe(false);

        store.loadEntity('12345');
        tick();
        expect(store.doEntitySettingsHaveUnsavedChanges()).toBe(false);

        store.setState({
            ...store.state,
            entity: {...store.state.entity, name: 'Modified name'},
        });
        expect(store.doEntitySettingsHaveUnsavedChanges()).toBe(true);
    }));

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

    it('should correctly create conversion pixel', fakeAsync(() => {
        const mockedConversionPixel: ConversionPixel = {
            id: '123',
            accountId: '12345',
            name: 'New conversion pixel',
            url: 'http://one.zemanta.com/pixel',
            lastTriggered: new Date(),
            impressions: 0,
            conversionWindows: [],
        };
        const goal: CampaignGoal = {
            id: '1',
            type: CampaignGoalKPI.CPA,
            value: '12.00',
            primary: true,
            conversionGoal: {
                type: CampaignConversionGoalType.PIXEL,
                conversionWindow: null,
                goalId: null,
                pixelUrl: null,
                name: null,
            },
        };

        const goals: CampaignGoal[] = [goal];
        store.updateState(goals, 'entity', 'goals');

        expect(store.state.entity.goals).toEqual(goals);
        expect(store.state.conversionPixels).toEqual([]);
        expect(store.state.conversionPixelsErrors).toEqual([]);

        conversionPixelsServiceStub.create.and
            .returnValue(of(mockedConversionPixel, asapScheduler))
            .calls.reset();

        store.createConversionPixel({
            campaignGoal: goal,
            conversionPixelName: 'New conversion pixel',
        });

        tick();

        expect(store.state.entity.goals).toEqual([
            {
                ...goal,
                conversionGoal: {
                    ...goal.conversionGoal,
                    goalId: mockedConversionPixel.id,
                },
            },
        ]);
        expect(store.state.conversionPixels).toEqual([mockedConversionPixel]);
        expect(store.state.conversionPixelsErrors).toEqual([]);
        expect(conversionPixelsServiceStub.create).toHaveBeenCalledTimes(1);
    }));

    it('should correctly handle errors when creating conversion pixel', fakeAsync(() => {
        const goal: CampaignGoal = {
            id: '1',
            type: CampaignGoalKPI.CPA,
            value: '12.00',
            primary: true,
            conversionGoal: {
                type: CampaignConversionGoalType.PIXEL,
                conversionWindow: null,
                goalId: null,
                pixelUrl: null,
                name: null,
            },
        };

        const goals: CampaignGoal[] = [goal];
        store.updateState(goals, 'entity', 'goals');

        expect(store.state.entity.goals).toEqual(goals);
        expect(store.state.conversionPixels).toEqual([]);
        expect(store.state.conversionPixelsErrors).toEqual([]);

        conversionPixelsServiceStub.create.and
            .returnValue(
                throwError({
                    message: 'Validation error',
                    error: {
                        details: {
                            name: ['Please specify conversion pixel name.'],
                        },
                    },
                })
            )
            .calls.reset();

        store.createConversionPixel({
            campaignGoal: goal,
            conversionPixelName: null,
        });

        tick();

        const conversionPixelsErrors = clone(
            store.state.conversionPixelsErrors
        );
        conversionPixelsErrors[store.state.entity.goals.indexOf(goal)] = {
            name: ['Please specify conversion pixel name.'],
        };

        expect(store.state.entity.goals).toEqual([goal]);
        expect(store.state.conversionPixels).toEqual([]);
        expect(store.state.conversionPixelsErrors).toEqual(
            conversionPixelsErrors
        );
        expect(conversionPixelsServiceStub.create).toHaveBeenCalledTimes(1);
    }));

    it('should correctly cancel conversion pixel creation', () => {
        const goal: CampaignGoal = {
            id: '1',
            type: CampaignGoalKPI.CPA,
            value: '12.00',
            primary: true,
            conversionGoal: {
                type: CampaignConversionGoalType.PIXEL,
                conversionWindow: null,
                goalId: null,
                pixelUrl: null,
                name: null,
            },
        };

        const goals: CampaignGoal[] = [goal];
        store.updateState(goals, 'entity', 'goals');

        const conversionPixelsErrors = clone(
            store.state.conversionPixelsErrors
        );
        conversionPixelsErrors[store.state.entity.goals.indexOf(goal)] = {
            name: ['Please specify conversion pixel name.'],
        };

        store.updateState(conversionPixelsErrors, 'conversionPixelsErrors');

        expect(store.state.entity.goals).toEqual(goals);
        expect(store.state.conversionPixels).toEqual([]);
        expect(store.state.conversionPixelsErrors).toEqual(
            conversionPixelsErrors
        );

        store.cancelConversionPixelCreation({
            campaignGoal: goal,
        });

        expect(store.state.entity.goals).toEqual(goals);
        expect(store.state.conversionPixels).toEqual([]);
        expect(store.state.conversionPixelsErrors).toEqual([]);
    });

    it('should correctly check if any account credit is available', () => {
        const accountCredits: AccountCredit[] = [
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

        store.updateState(accountCredits, 'extras', 'accountCredits');
        expect(store.isAnyAccountCreditAvailable()).toEqual(true);

        accountCredits[0].isAvailable = false;
        store.updateState(accountCredits, 'extras', 'accountCredits');
        expect(store.isAnyAccountCreditAvailable()).toEqual(false);
    });

    it('should correctly create campaign budget', () => {
        const accountCredits: AccountCredit[] = [
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

        expect(store.state.entity.budgets).toEqual([]);

        store.updateState(accountCredits, 'extras', 'accountCredits');
        store.createBudget();

        expect(store.state.entity.budgets.length).toEqual(1);
        expect(store.state.entity.budgets[0].creditId).toEqual(
            accountCredits[0].id
        );
    });

    it('should correctly update campaign budget', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue(of())
            .calls.reset();

        const comment = 'A generic comment';
        const budgets: CampaignBudget[] = [
            {
                id: '123',
                creditId: '100',
                startDate: new Date(1970, 2, 23),
                endDate: new Date(1970, 3, 10),
                amount: '1000000',
                margin: '200',
                comment: comment,
                canEditStartDate: true,
                canEditEndDate: false,
                canEditAmount: true,
            },
        ];

        store.updateState(budgets, 'entity', 'budgets');
        expect(store.state.entity.budgets[0].comment).toEqual(comment);

        const updatedComment = 'A new generic comment';
        const changeEvent: ChangeEvent<CampaignBudget> = {
            target: budgets[0],
            changes: {
                comment: updatedComment,
            },
        };

        store.updateBudget(changeEvent);
        expect(store.state.entity.budgets[0].comment).toEqual(updatedComment);
    });

    it('should correctly delete campaign budget', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue(of())
            .calls.reset();

        const budgets: CampaignBudget[] = [
            {
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
            },
        ];

        store.updateState(budgets, 'entity', 'budgets');
        expect(store.state.entity.budgets.length).toEqual(1);

        store.deleteBudget(budgets[0]);

        expect(store.state.entity.budgets.length).toEqual(0);
    });

    it('should correctly change campaign autopilot', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue(of())
            .calls.reset();

        store.updateState(false, 'entity', 'autopilot');
        expect(store.state.entity.autopilot).toEqual(false);
        store.setAutopilot(true);
        expect(store.state.entity.autopilot).toEqual(true);
    });
});
