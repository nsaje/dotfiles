import {asapScheduler, of} from 'rxjs';
import * as clone from 'clone';
import {EntitiesUpdatesService} from '../entities-updates.service';
import {
    EntityType,
    EntityUpdateAction,
    AdGroupState,
    AdState,
} from '../../../../app.constants';
import {tick, fakeAsync} from '@angular/core/testing';
import {RequestStateUpdater} from '../../../../shared/types/request-state-updater';
import * as mockHelpers from '../../../../testing/mock.helpers';
import {Campaign} from '../../types/campaign/campaign';
import {CampaignService} from './campaign.service';
import {CampaignEndpoint} from './campaign.endpoint';
import {CampaignWithExtras} from '../../types/campaign/campaign-with-extras';
import {CampaignExtras} from '../../types/campaign/campaign-extras';

describe('CampaignService', () => {
    let service: CampaignService;
    let campaignEndpointStub: jasmine.SpyObj<CampaignEndpoint>;
    let entitiesUpdatesServiceStub: jasmine.SpyObj<EntitiesUpdatesService>;
    let mockedCampaignWithExtras: CampaignWithExtras;
    let mockedCampaign: Campaign;
    let mockedCampaignExtras: CampaignExtras;
    let requestStateUpdater: RequestStateUpdater;

    beforeEach(() => {
        campaignEndpointStub = jasmine.createSpyObj(CampaignEndpoint.name, [
            'defaults',
            'get',
            'list',
            'validate',
            'create',
            'edit',
            'clone',
        ]);

        entitiesUpdatesServiceStub = jasmine.createSpyObj(
            EntitiesUpdatesService.name,
            ['registerEntityUpdate']
        );

        mockedCampaign = mockHelpers.getMockedCampaign();
        mockedCampaign.id = '12345';
        mockedCampaign.accountId = '12345';
        mockedCampaign.name = 'Test campaign';

        mockedCampaignExtras = mockHelpers.getMockedCampaignExtras();

        mockedCampaignWithExtras = {
            campaign: mockedCampaign,
            extras: mockedCampaignExtras,
        };

        service = new CampaignService(
            campaignEndpointStub,
            entitiesUpdatesServiceStub
        );

        requestStateUpdater = (requestName, requestState) => {};
    });

    it('should get default campaign via endpoint', () => {
        const mockedNewCampaignWithExtras = clone(mockedCampaignWithExtras);
        mockedNewCampaignWithExtras.campaign.id = null;
        mockedNewCampaignWithExtras.campaign.name = 'New campaign';

        campaignEndpointStub.defaults.and
            .returnValue(of(mockedNewCampaignWithExtras, asapScheduler))
            .calls.reset();

        service
            .defaults(mockedCampaign.accountId, requestStateUpdater)
            .subscribe(campaignWithExtras => {
                expect(campaignWithExtras.campaign).toEqual(
                    mockedNewCampaignWithExtras.campaign
                );
                expect(campaignWithExtras.extras).toEqual(
                    mockedNewCampaignWithExtras.extras
                );
            });
        expect(campaignEndpointStub.defaults).toHaveBeenCalledTimes(1);
        expect(campaignEndpointStub.defaults).toHaveBeenCalledWith(
            mockedCampaign.accountId,
            requestStateUpdater
        );
    });

    it('should get campaign via endpoint', () => {
        campaignEndpointStub.get.and
            .returnValue(of(mockedCampaignWithExtras, asapScheduler))
            .calls.reset();

        service
            .get(mockedCampaign.id, requestStateUpdater)
            .subscribe(campaignWithExtras => {
                expect(campaignWithExtras.campaign).toEqual(mockedCampaign);
                expect(campaignWithExtras.extras).toEqual(mockedCampaignExtras);
            });
        expect(campaignEndpointStub.get).toHaveBeenCalledTimes(1);
        expect(campaignEndpointStub.get).toHaveBeenCalledWith(
            mockedCampaign.id,
            requestStateUpdater
        );
    });

    it('should list campaigns via endpoint', () => {
        const mockedAgencyId = '114';
        const mockedAccountId = '92';
        const mockedOffset = 0;
        const mockedLimit = 20;
        const mockedKeyword = 'keyword';

        campaignEndpointStub.list.and
            .returnValue(of([mockedCampaign], asapScheduler))
            .calls.reset();

        service
            .list(
                mockedAgencyId,
                mockedAccountId,
                mockedOffset,
                mockedLimit,
                mockedKeyword,
                requestStateUpdater
            )
            .subscribe(adGroups => {
                expect(adGroups).toEqual([mockedCampaign]);
            });
        expect(campaignEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(campaignEndpointStub.list).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedAccountId,
            mockedOffset,
            mockedLimit,
            mockedKeyword,
            requestStateUpdater
        );
    });

    it('should save new campaign and register entity update', fakeAsync(() => {
        campaignEndpointStub.create.and
            .returnValue(of(mockedCampaign, asapScheduler))
            .calls.reset();

        const mockedNewCampaign = clone(mockedCampaign);
        mockedNewCampaign.id = null;
        service
            .save(mockedNewCampaign, requestStateUpdater)
            .subscribe(campaign => {
                expect(campaign).toEqual(mockedCampaign);
            });
        tick();

        expect(campaignEndpointStub.create).toHaveBeenCalledTimes(1);
        expect(campaignEndpointStub.create).toHaveBeenCalledWith(
            mockedNewCampaign,
            requestStateUpdater
        );
        expect(campaignEndpointStub.edit).not.toHaveBeenCalled();
        expect(
            entitiesUpdatesServiceStub.registerEntityUpdate
        ).toHaveBeenCalledWith({
            id: mockedCampaign.id,
            type: EntityType.CAMPAIGN,
            action: EntityUpdateAction.CREATE,
        });
    }));

    it('should edit existing campaign and register entity update', fakeAsync(() => {
        campaignEndpointStub.edit.and
            .returnValue(of(mockedCampaign, asapScheduler))
            .calls.reset();

        service
            .save(mockedCampaign, requestStateUpdater)
            .subscribe(campaign => {
                expect(campaign).toEqual(mockedCampaign);
            });
        tick();

        expect(campaignEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(campaignEndpointStub.edit).toHaveBeenCalledWith(
            mockedCampaign,
            requestStateUpdater
        );
        expect(campaignEndpointStub.create).not.toHaveBeenCalled();
        expect(
            entitiesUpdatesServiceStub.registerEntityUpdate
        ).toHaveBeenCalledWith({
            id: mockedCampaign.id,
            type: EntityType.CAMPAIGN,
            action: EntityUpdateAction.EDIT,
        });
    }));

    it('should archive campaign and register entity update', fakeAsync(() => {
        campaignEndpointStub.edit.and
            .returnValue(of({...mockedCampaign, archived: true}, asapScheduler))
            .calls.reset();

        service.archive(mockedCampaign.id, requestStateUpdater).subscribe();
        tick();

        expect(campaignEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(campaignEndpointStub.edit).toHaveBeenCalledWith(
            {
                id: mockedCampaign.id,
                archived: true,
            },
            requestStateUpdater
        );
        expect(
            entitiesUpdatesServiceStub.registerEntityUpdate
        ).toHaveBeenCalledWith({
            id: mockedCampaign.id,
            type: EntityType.CAMPAIGN,
            action: EntityUpdateAction.ARCHIVE,
        });
    }));

    it('should clone campaign via endpoint', fakeAsync(() => {
        campaignEndpointStub.clone.and
            .returnValue(of(mockedCampaign, asapScheduler))
            .calls.reset();

        service
            .clone(
                mockedCampaign.id,
                {
                    destinationCampaignName: 'Test campaign clone',
                    cloneAdGroups: true,
                    cloneAds: true,
                    adGroupStateOverride: AdGroupState.ACTIVE,
                    adStateOverride: AdState.ACTIVE,
                },
                requestStateUpdater
            )
            .subscribe(campaign => {
                expect(campaign).toEqual(mockedCampaign);
            });
        tick();

        expect(campaignEndpointStub.clone).toHaveBeenCalledTimes(1);
        expect(campaignEndpointStub.clone).toHaveBeenCalledWith(
            mockedCampaign.id,
            {
                destinationCampaignName: 'Test campaign clone',
                cloneAdGroups: true,
                cloneAds: true,
                adGroupStateOverride: AdGroupState.ACTIVE,
                adStateOverride: AdState.ACTIVE,
            },
            requestStateUpdater
        );
    }));
});
