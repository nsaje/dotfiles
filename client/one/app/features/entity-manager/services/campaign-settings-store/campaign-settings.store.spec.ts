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
    CreditStatus,
    Currency,
    CampaignType,
    IabCategory,
    Language,
    GaTrackingType,
} from '../../../../app.constants';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {of, asapScheduler, throwError} from 'rxjs';
import {ConversionPixelsService} from '../../../../core/conversion-pixels/services/conversion-pixels.service';
import {fakeAsync, tick} from '@angular/core/testing';
import {CampaignSettingsStoreFieldsErrorsState} from './campaign-settings.store.fields-errors-state';
import {ConversionPixel} from '../../../../core/conversion-pixels/types/conversion-pixel';
import {Credit} from '../../../../core/credits/types/credit';
import {CampaignBudget} from '../../../../core/entities/types/campaign/campaign-budget';
import {CampaignTracking} from '../../../../core/entities/types/campaign/campaign-tracking';
import {DealsService} from '../../../../core/deals/services/deals.service';
import {Deal} from '../../../../core/deals/types/deal';
import {SourcesService} from '../../../../core/sources/services/sources.service';
import {Source} from '../../../../core/sources/types/source';

describe('CampaignSettingsStore', () => {
    let campaignServiceStub: jasmine.SpyObj<CampaignService>;
    let conversionPixelsServiceStub: jasmine.SpyObj<ConversionPixelsService>;
    let dealsServiceStub: jasmine.SpyObj<DealsService>;
    let sourcesServiceStub: jasmine.SpyObj<SourcesService>;
    let store: CampaignSettingsStore;
    let campaignWithExtras: CampaignWithExtras;
    let campaign: Campaign;
    let campaignExtras: CampaignExtras;
    let conversionPixels: ConversionPixel[];
    let mockedSources: Source[];

    beforeEach(() => {
        campaignServiceStub = jasmine.createSpyObj(CampaignService.name, [
            'defaults',
            'get',
            'validate',
            'save',
            'archive',
        ]);
        dealsServiceStub = jasmine.createSpyObj(DealsService.name, ['list']);
        sourcesServiceStub = jasmine.createSpyObj(SourcesService.name, [
            'list',
        ]);
        conversionPixelsServiceStub = jasmine.createSpyObj(
            ConversionPixelsService.name,
            ['list', 'create', 'edit']
        );

        store = new CampaignSettingsStore(
            campaignServiceStub,
            conversionPixelsServiceStub,
            dealsServiceStub,
            sourcesServiceStub
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

        mockedSources = [
            {slug: 'smaato', name: 'Smaato', released: true, deprecated: false},
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

        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
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
        expect(store.state.sources).toEqual(mockedSources);

        expect(campaignServiceStub.defaults).toHaveBeenCalledTimes(1);
        expect(conversionPixelsServiceStub.list).toHaveBeenCalledTimes(1);
        expect(sourcesServiceStub.list).toHaveBeenCalledTimes(1);
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

        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
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
        expect(store.state.sources).toEqual(mockedSources);

        expect(campaignServiceStub.get).toHaveBeenCalledTimes(1);
        expect(conversionPixelsServiceStub.list).toHaveBeenCalledTimes(1);
        expect(sourcesServiceStub.list).toHaveBeenCalledTimes(1);
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
                    status: 400,
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
        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
            .calls.reset();

        store.loadEntity('12345');
        tick();

        store.saveEntity();
        tick();

        expect(store.state.entity).toEqual(mockedCampaignWithExtras.campaign);
        expect(store.state.sources).toEqual(mockedSources);
        expect(store.state.fieldsErrors).toEqual(
            new CampaignSettingsStoreFieldsErrorsState()
        );
        expect(campaignServiceStub.save).toHaveBeenCalledTimes(1);
        expect(sourcesServiceStub.list).toHaveBeenCalledTimes(1);
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
                    status: 400,
                    message: 'Validation error',
                    error: {
                        details: {name: ['Please specify campaign name.']},
                    },
                })
            )
            .calls.reset();
        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
            .calls.reset();

        store.loadEntity('12345');
        tick();

        store.saveEntity();
        tick();

        expect(store.state.entity).toEqual(mockedCampaignWithExtras.campaign);
        expect(store.state.sources).toEqual(mockedSources);
        expect(store.state.fieldsErrors).toEqual(
            jasmine.objectContaining({
                ...new CampaignSettingsStoreFieldsErrorsState(),
                name: ['Please specify campaign name.'],
            })
        );
        expect(campaignServiceStub.save).toHaveBeenCalledTimes(1);
        expect(sourcesServiceStub.list).toHaveBeenCalledTimes(1);
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
        sourcesServiceStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
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
            .and.returnValue()
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
        store.patchState(goals, 'entity', 'goals');
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
            .and.returnValue()
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
        store.patchState(goals, 'entity', 'goals');
        expect(store.state.entity.goals).toEqual(goals);
        expect(store.state.entity.goals[0].primary).toEqual(true);
        expect(store.state.entity.goals[1].primary).toEqual(false);
        store.setPrimaryGoal(goals[1]);
        expect(store.state.entity.goals[0].primary).toEqual(false);
        expect(store.state.entity.goals[1].primary).toEqual(true);
    });

    it('should correctly change goal', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
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
        store.patchState(goals, 'entity', 'goals');
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
            .and.returnValue()
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
        store.patchState(goals, 'entity', 'goals');
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
        store.patchState(goals, 'entity', 'goals');

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
        store.patchState(goals, 'entity', 'goals');

        expect(store.state.entity.goals).toEqual(goals);
        expect(store.state.conversionPixels).toEqual([]);
        expect(store.state.conversionPixelsErrors).toEqual([]);

        conversionPixelsServiceStub.create.and
            .returnValue(
                throwError({
                    status: 400,
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
        store.patchState(goals, 'entity', 'goals');

        const conversionPixelsErrors = clone(
            store.state.conversionPixelsErrors
        );
        conversionPixelsErrors[store.state.entity.goals.indexOf(goal)] = {
            name: ['Please specify conversion pixel name.'],
        };

        store.patchState(conversionPixelsErrors, 'conversionPixelsErrors');

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

    it('should correctly check if any credit is available', () => {
        const credits: Credit[] = [
            {
                id: '100',
                createdOn: new Date(1970, 1, 21),
                status: CreditStatus.SIGNED,
                agencyId: '123',
                accountId: null,
                startDate: new Date(1970, 2, 21),
                endDate: new Date(1970, 3, 21),
                licenseFee: '0.1305',
                serviceFee: '0.1305',
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

        store.patchState(credits, 'extras', 'credits');
        expect(store.isAnyCreditAvailable()).toEqual(true);

        credits[0].isAvailable = false;
        store.patchState(credits, 'extras', 'credits');
        expect(store.isAnyCreditAvailable()).toEqual(false);
    });

    it('should correctly create campaign budget', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        const credits: Credit[] = [
            {
                id: '100',
                createdOn: new Date(1970, 1, 21),
                status: CreditStatus.SIGNED,
                agencyId: '123',
                accountId: null,
                startDate: new Date(1970, 2, 21),
                endDate: new Date(1970, 3, 21),
                licenseFee: '0.1305',
                serviceFee: '0.1305',
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

        expect(store.state.entity.budgets).toEqual([]);

        store.patchState(credits, 'extras', 'credits');
        store.createBudget();

        expect(store.state.entity.budgets.length).toEqual(1);
        expect(store.state.entity.budgets[0].creditId).toEqual(credits[0].id);
    });

    it('should correctly update campaign budget', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        const comment = 'A generic comment';
        const budgets: CampaignBudget[] = [
            {
                id: '123',
                creditId: '100',
                accountId: '123',
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

        store.patchState(budgets, 'entity', 'budgets');
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
            .and.returnValue()
            .calls.reset();

        const budgets: CampaignBudget[] = [
            {
                id: '123',
                creditId: '100',
                accountId: '123',
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

        store.patchState(budgets, 'entity', 'budgets');
        expect(store.state.entity.budgets.length).toEqual(1);

        store.deleteBudget(budgets[0]);

        expect(store.state.entity.budgets.length).toEqual(0);
    });

    it('should correctly change campaign name', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState('Generic name', 'entity', 'name');
        expect(store.state.entity.name).toEqual('Generic name');
        store.setName('Generic name 2');
        expect(store.state.entity.name).toEqual('Generic name 2');
    });

    it('should correctly change campaign type', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState(CampaignType.CONTENT, 'entity', 'type');
        expect(store.state.entity.type).toEqual(CampaignType.CONTENT);
        store.setType(CampaignType.DISPLAY);
        expect(store.state.entity.type).toEqual(CampaignType.DISPLAY);
    });

    it('should correctly change campaign manager', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState('11', 'entity', 'campaignManager');
        expect(store.state.entity.campaignManager).toEqual('11');
        store.setCampaignManager('12');
        expect(store.state.entity.campaignManager).toEqual('12');
    });

    it('should correctly change iab-category', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState(IabCategory.IAB1, 'entity', 'iabCategory');
        expect(store.state.entity.iabCategory).toEqual(IabCategory.IAB1);
        store.setIabCategory(IabCategory.IAB10_1);
        expect(store.state.entity.iabCategory).toEqual(IabCategory.IAB10_1);
    });

    it('should correctly change language', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState(Language.ENGLISH, 'entity', 'language');
        expect(store.state.entity.language).toEqual(Language.ENGLISH);
        store.setLanguage(Language.ITALIAN);
        expect(store.state.entity.language).toEqual(Language.ITALIAN);
    });

    it('should correctly change frequency capping', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState(22, 'entity', 'frequencyCapping');
        expect(store.state.entity.frequencyCapping).toEqual(22);
        store.setFrequencyCapping('30');
        expect(store.state.entity.frequencyCapping).toEqual(30);
    });

    it('should correctly set publisher groups', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();
        const $event: any = {
            whitelistedPublisherGroups: [123, 456, 789],
            blacklistedPublisherGroups: [],
        };

        expect(store.state.entity.targeting.publisherGroups).toEqual({
            included: [],
            excluded: [],
        });

        store.setPublisherGroupsTargeting($event);

        expect(store.state.entity.targeting.publisherGroups).toEqual({
            included: $event.whitelistedPublisherGroups,
            excluded: $event.blacklistedPublisherGroups,
        });
    });

    it('should correctly change campaign autopilot', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.patchState(false, 'entity', 'autopilot');
        expect(store.state.entity.autopilot).toEqual(false);
        store.setAutopilot(true);
        expect(store.state.entity.autopilot).toEqual(true);
    });

    it('should correctly change campaign tracking', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        const tracking: CampaignTracking = {
            ga: {
                enabled: true,
                type: GaTrackingType.EMAIL,
                webPropertyId: 'Generic web id',
            },
            adobe: {
                enabled: false,
                trackingParameter: null,
            },
        };

        store.patchState(tracking, 'entity', 'tracking');
        expect(store.state.entity.tracking).toEqual(tracking);

        const changeEvent: ChangeEvent<CampaignTracking> = {
            target: tracking,
            changes: {
                ga: {
                    ...tracking.ga,
                    enabled: false,
                },
            },
        };

        store.changeCampaignTracking(changeEvent);
        expect(store.state.entity.tracking.ga.enabled).toEqual(false);
    });

    it('should correctly load available deals via deals service', fakeAsync(() => {
        const mockedKeyword = 'bla';
        const mockedAvailableDeals: Deal[] = [];

        dealsServiceStub.list.and
            .returnValue(of(mockedAvailableDeals, asapScheduler))
            .calls.reset();

        store.loadAvailableDeals(mockedKeyword);
        tick();

        expect(dealsServiceStub.list).toHaveBeenCalledTimes(1);
        expect(store.state.availableDeals).toEqual(mockedAvailableDeals);
    }));

    it('should correctly add deal', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        const mockedDeal: Deal = {
            id: '10000000',
            dealId: '45345',
            agencyId: '45',
            agencyName: 'Test agency',
            accountId: null,
            accountName: null,
            description: 'test directDeal',
            name: 'test directDeal',
            source: 'urska',
            floorPrice: '0.0002',
            createdDt: new Date(),
            modifiedDt: new Date(),
            createdBy: 'test@test.com',
            numOfAccounts: 0,
            numOfCampaigns: 0,
            numOfAdgroups: 0,
        };
        store.addDeal(mockedDeal);

        expect(store.state.entity.deals).toEqual([mockedDeal]);
    });

    it('should correctly remove deal', () => {
        spyOn(store, 'validateEntity')
            .and.returnValue()
            .calls.reset();

        store.state.entity.deals = [
            {
                id: '10000000',
                dealId: '45345',
                agencyId: '45',
                agencyName: 'Test agency',
                accountId: null,
                accountName: null,
                description: 'test directDeal',
                name: 'test directDeal',
                source: 'urska',
                floorPrice: '0.0002',
                createdDt: new Date(),
                modifiedDt: new Date(),
                createdBy: 'test@test.com',
                numOfAccounts: 0,
                numOfCampaigns: 0,
                numOfAdgroups: 0,
            },
        ];

        store.removeDeal(store.state.entity.deals[0]);
        expect(store.state.entity.deals).toEqual([]);
    });
});
