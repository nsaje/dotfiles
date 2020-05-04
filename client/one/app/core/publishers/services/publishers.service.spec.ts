import {of} from 'rxjs';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {PublishersEndpoint} from './publishers.endpoint';
import {PublishersService} from './publishers.service';
import {PublisherInfo} from '../types/publisher-info';
import {
    PublisherBlacklistLevel,
    PublisherTargetingStatus,
} from '../../../app.constants';
import {fakeAsync, tick} from '@angular/core/testing';

describe('PublishersService', () => {
    let service: PublishersService;
    let endpointStub: jasmine.SpyObj<PublishersEndpoint>;
    let zemPermissionsStub: any;
    let requestStateUpdater: RequestStateUpdater;

    let mockedPublisherRows: PublisherInfo[];
    let mockedPlacementRows: PublisherInfo[];
    let mockedStatus: PublisherTargetingStatus;
    let mockedLevel: PublisherBlacklistLevel;
    let mockedEntityId: number;
    let hasGlobalBlacklistPermission: boolean;

    beforeEach(() => {
        endpointStub = jasmine.createSpyObj(PublishersEndpoint.name, [
            'updateBlacklistStatuses',
        ]);
        zemPermissionsStub = {
            hasPermission: (permission: string) => {
                if (
                    permission ===
                    'zemauth.can_access_global_publisher_blacklist_status'
                ) {
                    return hasGlobalBlacklistPermission;
                } else {
                    return true;
                }
            },
        };
        endpointStub.updateBlacklistStatuses.and.returnValue(of(true));
        service = new PublishersService(endpointStub, zemPermissionsStub);
        requestStateUpdater = (requestName, requestState) => {};

        mockedPublisherRows = [
            {
                sourceId: 12,
                sourceSlug: '12',
                publisher: 'www.zemanta.com',
            },
            {
                sourceId: 34,
                sourceSlug: '34',
                publisher: 'www.outbrain.com',
            },
        ];

        mockedPlacementRows = [
            {
                sourceId: 12,
                sourceSlug: '12',
                publisher: 'www.zemanta.com',
                placement: '00000000-0008-d469-0000-000000000106',
            },
            {
                sourceId: 34,
                sourceSlug: '34',
                publisher: 'www.outbrain.com',
                placement: '00000000-0008-d469-0000-000000000107',
            },
        ];
        mockedStatus = PublisherTargetingStatus.BLACKLISTED;
        mockedLevel = PublisherBlacklistLevel.ACCOUNT;
        mockedEntityId = 123;
        hasGlobalBlacklistPermission = true;
    });

    it('should correctly call the updateBlacklistStatuses endpoint function on the account level', fakeAsync(() => {
        service.updateBlacklistStatuses(
            mockedPublisherRows,
            mockedStatus,
            mockedLevel,
            mockedEntityId,
            requestStateUpdater
        );
        tick();

        expect(endpointStub.updateBlacklistStatuses).toHaveBeenCalledWith(
            {
                entries: [
                    {
                        source: '12',
                        publisher: 'www.zemanta.com',
                        includeSubdomains: true,
                    },
                    {
                        source: '34',
                        publisher: 'www.outbrain.com',
                        includeSubdomains: true,
                    },
                ],
                status: mockedStatus,
                account: mockedEntityId,
            },
            requestStateUpdater
        );
    }));

    it('should correctly call the updateBlacklistStatuses endpoint function for placements', fakeAsync(() => {
        service.updateBlacklistStatuses(
            mockedPlacementRows,
            mockedStatus,
            mockedLevel,
            mockedEntityId,
            requestStateUpdater
        );
        tick();

        expect(endpointStub.updateBlacklistStatuses).toHaveBeenCalledWith(
            {
                entries: [
                    {
                        source: '12',
                        publisher: 'www.zemanta.com',
                        includeSubdomains: true,
                        placement: '00000000-0008-d469-0000-000000000106',
                    },
                    {
                        source: '34',
                        publisher: 'www.outbrain.com',
                        includeSubdomains: true,
                        placement: '00000000-0008-d469-0000-000000000107',
                    },
                ],
                status: mockedStatus,
                account: mockedEntityId,
            },
            requestStateUpdater
        );
    }));

    it('should not set the includeSubdomains attribute when setting the UNLISTED status', fakeAsync(() => {
        service.updateBlacklistStatuses(
            mockedPublisherRows,
            PublisherTargetingStatus.UNLISTED,
            mockedLevel,
            mockedEntityId,
            requestStateUpdater
        );
        tick();

        expect(endpointStub.updateBlacklistStatuses).toHaveBeenCalledWith(
            {
                entries: [
                    {
                        source: '12',
                        publisher: 'www.zemanta.com',
                    },
                    {
                        source: '34',
                        publisher: 'www.outbrain.com',
                    },
                ],
                status: PublisherTargetingStatus.UNLISTED,
                account: mockedEntityId,
            },
            requestStateUpdater
        );
    }));

    it('should correctly call the updateBlacklistStatuses endpoint function on the campaign level', fakeAsync(() => {
        service.updateBlacklistStatuses(
            mockedPublisherRows,
            mockedStatus,
            PublisherBlacklistLevel.CAMPAIGN,
            mockedEntityId,
            requestStateUpdater
        );
        tick();

        expect(endpointStub.updateBlacklistStatuses).toHaveBeenCalledWith(
            {
                entries: [
                    {
                        source: '12',
                        publisher: 'www.zemanta.com',
                        includeSubdomains: true,
                    },
                    {
                        source: '34',
                        publisher: 'www.outbrain.com',
                        includeSubdomains: true,
                    },
                ],
                status: mockedStatus,
                campaign: mockedEntityId,
            },
            requestStateUpdater
        );
    }));

    it('should correctly call the updateBlacklistStatuses endpoint function on the ad group level', fakeAsync(() => {
        service.updateBlacklistStatuses(
            mockedPublisherRows,
            mockedStatus,
            PublisherBlacklistLevel.ADGROUP,
            mockedEntityId,
            requestStateUpdater
        );
        tick();

        expect(endpointStub.updateBlacklistStatuses).toHaveBeenCalledWith(
            {
                entries: [
                    {
                        source: '12',
                        publisher: 'www.zemanta.com',
                        includeSubdomains: true,
                    },
                    {
                        source: '34',
                        publisher: 'www.outbrain.com',
                        includeSubdomains: true,
                    },
                ],
                status: mockedStatus,
                adGroup: mockedEntityId,
            },
            requestStateUpdater
        );
    }));

    it('should correctly call the updateBlacklistStatuses endpoint function on the global level', fakeAsync(() => {
        service.updateBlacklistStatuses(
            mockedPublisherRows,
            mockedStatus,
            PublisherBlacklistLevel.GLOBAL,
            undefined,
            requestStateUpdater
        );
        tick();

        expect(endpointStub.updateBlacklistStatuses).toHaveBeenCalledWith(
            {
                entries: [
                    {
                        source: '12',
                        publisher: 'www.zemanta.com',
                        includeSubdomains: true,
                    },
                    {
                        source: '34',
                        publisher: 'www.outbrain.com',
                        includeSubdomains: true,
                    },
                ],
                status: mockedStatus,
            },
            requestStateUpdater
        );
    }));

    it('should return a list of possible blacklist actions', fakeAsync(() => {
        expect(service.getBlacklistActions()).toEqual([
            {
                name: 'Add to',
                status: PublisherTargetingStatus.BLACKLISTED,
            },
            {
                name: 'Remove from',
                status: PublisherTargetingStatus.UNLISTED,
            },
        ]);
    }));

    it('should return a list of possible blacklist levels', fakeAsync(() => {
        expect(service.getBlacklistLevels(1, 2, 3)).toEqual([
            {
                name: 'ad group',
                level: PublisherBlacklistLevel.ADGROUP,
            },
            {
                name: 'campaign',
                level: PublisherBlacklistLevel.CAMPAIGN,
            },
            {
                name: 'account',
                level: PublisherBlacklistLevel.ACCOUNT,
            },
            {
                name: 'global',
                level: PublisherBlacklistLevel.GLOBAL,
                permissions: [
                    'zemauth.can_access_global_publisher_blacklist_status',
                ],
            },
        ]);
    }));

    it("should not return global blacklist level if the user hasn't got the correct permission", fakeAsync(() => {
        hasGlobalBlacklistPermission = false;
        expect(service.getBlacklistLevels(1, 2, 3)).toEqual([
            {
                name: 'ad group',
                level: PublisherBlacklistLevel.ADGROUP,
            },
            {
                name: 'campaign',
                level: PublisherBlacklistLevel.CAMPAIGN,
            },
            {
                name: 'account',
                level: PublisherBlacklistLevel.ACCOUNT,
            },
        ]);
    }));

    it('should not return levels without supplied IDs', fakeAsync(() => {
        hasGlobalBlacklistPermission = false;
        expect(service.getBlacklistLevels(1, undefined, undefined)).toEqual([
            {
                name: 'account',
                level: PublisherBlacklistLevel.ACCOUNT,
            },
        ]);
    }));
});
