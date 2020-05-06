import {
    PublisherBlacklistLevel,
    PublisherTargetingStatus,
} from '../../../../../../../app.constants';
import {fakeAsync, tick} from '@angular/core/testing';
import {BulkBlacklistActionsStore} from './bulk-blacklist-actions.store';
import {PublishersService} from '../../../../../../../core/publishers/services/publishers.service';
import {PublisherInfo} from '../../../../../../../core/publishers/types/publisher-info';
import {of} from 'rxjs';

describe('BulkBlacklistActionsStore', () => {
    let serviceStub: jasmine.SpyObj<PublishersService>;
    let store: BulkBlacklistActionsStore;

    let mockedPublisherRows: PublisherInfo[];
    let mockedPlacementRows: PublisherInfo[];
    let mockedStatus: PublisherTargetingStatus;
    let mockedLevel: PublisherBlacklistLevel;
    let mockedEntityId: number;

    beforeEach(() => {
        serviceStub = jasmine.createSpyObj(PublishersService.name, [
            'updateBlacklistStatuses',
        ]);
        serviceStub.updateBlacklistStatuses.and.returnValue(of(true));
        store = new BulkBlacklistActionsStore(serviceStub);

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
    });

    it('should correctly call the updateBlacklistStatuses service function for publishers', fakeAsync(() => {
        store.updateBlacklistStatuses(
            mockedPublisherRows,
            mockedStatus,
            mockedLevel,
            mockedEntityId
        );
        tick();

        expect(serviceStub.updateBlacklistStatuses).toHaveBeenCalledWith(
            mockedPublisherRows,
            mockedStatus,
            mockedLevel,
            mockedEntityId,
            jasmine.any(Function)
        );
    }));

    it('should correctly call the updateBlacklistStatuses service function for placements', fakeAsync(() => {
        store.updateBlacklistStatuses(
            mockedPlacementRows,
            mockedStatus,
            mockedLevel,
            mockedEntityId
        );
        tick();

        expect(serviceStub.updateBlacklistStatuses).toHaveBeenCalledWith(
            mockedPlacementRows,
            mockedStatus,
            mockedLevel,
            mockedEntityId,
            jasmine.any(Function)
        );
    }));
});
