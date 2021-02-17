import {asapScheduler, of} from 'rxjs';
import * as clone from 'clone';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {CreativesEndpoint} from './creatives.endpoint';
import {CreativesService} from './creatives.service';
import {Creative} from '../types/creative';
import {
    AdType,
    CreativeBatchMode,
    CreativeBatchType,
} from '../../../app.constants';
import {TrackerEventType, TrackerMethod} from '../creatives.constants';
import {CreativeBatch} from '../types/creative-batch';
import {CreativeBatchStatus} from '../types/creative-batch-status';
import {fakeAsync, tick} from '@angular/core/testing';
import {CreativeCandidate} from '../types/creative-candidate';

describe('CreativesService', () => {
    let service: CreativesService;
    let creativesEndpointStub: jasmine.SpyObj<CreativesEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    let mockedCreative: Creative;
    let mockedCreatives: Creative[];
    let mockedAgencyId: string;
    let mockedAccountId: string;
    let mockedBatch: CreativeBatch;
    let mockedBatchId: string;
    let mockedBatchCreateParams: CreativeBatch;
    let mockedCreativeCandidateId: string;
    let mockedCandidateCreateParams: CreativeCandidate;
    let mockedCreativeCandidate: CreativeCandidate;
    let mockedCreativeCandidates: CreativeCandidate[];

    beforeEach(() => {
        creativesEndpointStub = jasmine.createSpyObj(CreativesEndpoint.name, [
            'list',
            'getBatch',
            'createBatch',
            'editBatch',
            'validateBatch',
            'listCandidates',
            'createCandidate',
            'getCandidate',
            'editCandidate',
        ]);
        service = new CreativesService(creativesEndpointStub);
        requestStateUpdater = (requestName, requestState) => {};

        mockedAgencyId = '71';
        mockedAccountId = '55';
        mockedCreatives = [
            {
                id: '10000000',
                agencyId: '71',
                agencyName: 'Test agency',
                accountId: null,
                accountName: null,
                type: AdType.CONTENT,
                url: 'https://one.zemanta.com',
                title: 'Test',
                displayUrl: 'https://one.zemanta.com',
                brandName: 'Zemanta',
                description: 'Best advertising platform ever',
                callToAction: 'Advertise now!',
                tags: ['zemanta', 'native', 'advertising'],
                displayHostedImageUrl: 'http://placekitten.com/200/300',
                hostedImageUrl: 'http://placekitten.com/300/300',
                landscapeHostedImageUrl: 'http://placekitten.com/720/450',
                portraitHostedImageUrl: 'http://placekitten.com/375/480',
                hostedIconUrl: 'http://placekitten.com/64/64',
                imageWidth: null,
                imageHeight: null,
                adTag: 'adTag',
                videoAssetId: '123',
                trackers: [
                    {
                        eventType: TrackerEventType.IMPRESSION,
                        method: TrackerMethod.IMG,
                        url: 'https://test.com',
                        fallbackUrl: 'http://test.com',
                        trackerOptional: false,
                    },
                ],
            },
        ];
        mockedCreative = clone(mockedCreatives[0]);

        mockedBatchId = '1';
        mockedBatch = {
            id: mockedBatchId,
            agencyId: '71',
            accountId: null,
            type: CreativeBatchType.NATIVE,
            mode: CreativeBatchMode.INSERT,
            name: 'Test batch',
            status: CreativeBatchStatus.IN_PROGRESS,
            tags: ['test'],
            imageCrop: 'what',
            displayUrl: 'https://one.zemanta.com',
            brandName: 'TestBrand',
            description: 'A very testfully testful brand',
            callToAction: 'Just do it',
            createdBy: 'Nobody',
            createdDt: new Date(),
        };

        mockedBatchCreateParams = {
            name: 'Test batch',
            agencyId: '71',
            accountId: null,
            type: CreativeBatchType.NATIVE,
            mode: CreativeBatchMode.INSERT,
        };

        mockedCreativeCandidates = [
            {
                id: '10000000',
                type: AdType.CONTENT,
                url: 'https://one.zemanta.com',
                title: 'Test candidate',
                displayUrl: 'https://one.zemanta.com',
                brandName: 'Zemanta',
                description: 'Best advertising platform ever',
                callToAction: 'Advertise now!',
                tags: ['zemanta', 'native', 'advertising'],
                imageUrl: 'http://placekitten.com/200/300',
                iconUrl: 'http://placekitten.com/64/64',
                adTag: 'adTag',
                videoAssetId: '123',
                trackers: [
                    {
                        eventType: TrackerEventType.IMPRESSION,
                        method: TrackerMethod.IMG,
                        url: 'https://test.com',
                        fallbackUrl: 'http://test.com',
                        trackerOptional: false,
                    },
                ],
            },
        ];

        mockedCandidateCreateParams = {
            title: 'Test candidate',
        };

        mockedCreativeCandidate = mockedCreativeCandidates[0];
        mockedCreativeCandidateId = mockedCreativeCandidate.id;
    });

    it('should get creatives via endpoint', () => {
        const limit = 10;
        const offset = 0;
        const keyword = 'blue';
        const agencyOnly = true;
        const creativeType = AdType.CONTENT;
        const tags = ['a', 'b', 'c'];
        creativesEndpointStub.list.and
            .returnValue(of(mockedCreatives, asapScheduler))
            .calls.reset();

        service
            .list(
                mockedAgencyId,
                mockedAccountId,
                offset,
                limit,
                keyword,
                creativeType,
                tags,
                requestStateUpdater
            )
            .subscribe(creatives => {
                expect(creatives).toEqual(mockedCreatives);
            });
        expect(creativesEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(creativesEndpointStub.list).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedAccountId,
            offset,
            limit,
            keyword,
            creativeType,
            tags,
            requestStateUpdater
        );
    });

    it('should get creative batch via endpoint', () => {
        creativesEndpointStub.getBatch.and
            .returnValue(of(mockedBatch, asapScheduler))
            .calls.reset();

        service
            .getBatch(mockedBatchId, requestStateUpdater)
            .subscribe(batch => {
                expect(batch).toEqual(mockedBatch);
            });
        expect(creativesEndpointStub.getBatch).toHaveBeenCalledTimes(1);
        expect(creativesEndpointStub.getBatch).toHaveBeenCalledWith(
            mockedBatchId,
            requestStateUpdater
        );
    });

    it('should create new creative batch', fakeAsync(() => {
        creativesEndpointStub.createBatch.and
            .returnValue(of(mockedBatch, asapScheduler))
            .calls.reset();

        const mockedNewBatch = clone(mockedBatchCreateParams);
        service
            .createBatch(mockedNewBatch, requestStateUpdater)
            .subscribe(batch => {
                expect(batch).toEqual(mockedBatch);
            });
        tick();

        expect(creativesEndpointStub.createBatch).toHaveBeenCalledTimes(1);
        expect(creativesEndpointStub.createBatch).toHaveBeenCalledWith(
            mockedNewBatch,
            requestStateUpdater
        );
    }));

    it('should edit creative batch via endpoint', () => {
        const mockedNewBatch = clone(mockedBatch);
        creativesEndpointStub.editBatch.and
            .returnValue(of(mockedBatch, asapScheduler))
            .calls.reset();

        service
            .editBatch(mockedNewBatch, requestStateUpdater)
            .subscribe(newBatch => {
                expect(newBatch).toEqual(mockedNewBatch);
            });

        expect(creativesEndpointStub.editBatch).toHaveBeenCalledTimes(1);
        expect(creativesEndpointStub.editBatch).toHaveBeenCalledWith(
            mockedNewBatch,
            requestStateUpdater
        );
    });

    it('should validate creative batch via endpoint', () => {
        creativesEndpointStub.validateBatch.and
            .returnValue(of(null, asapScheduler))
            .calls.reset();

        service
            .validateBatch(mockedBatch, requestStateUpdater)
            .subscribe(x => {});
        expect(creativesEndpointStub.validateBatch).toHaveBeenCalledTimes(1);
        expect(creativesEndpointStub.validateBatch).toHaveBeenCalledWith(
            mockedBatch,
            requestStateUpdater
        );
    });

    it('should get creative candidates via endpoint', () => {
        const limit = 10;
        const offset = 0;
        creativesEndpointStub.listCandidates.and
            .returnValue(of(mockedCreativeCandidates, asapScheduler))
            .calls.reset();

        service
            .listCandidates(mockedBatchId, offset, limit, requestStateUpdater)
            .subscribe(candidates => {
                expect(candidates).toEqual(mockedCreativeCandidates);
            });
        expect(creativesEndpointStub.listCandidates).toHaveBeenCalledTimes(1);
        expect(creativesEndpointStub.listCandidates).toHaveBeenCalledWith(
            mockedBatchId,
            offset,
            limit,
            requestStateUpdater
        );
    });

    it('should create new creative candidate', fakeAsync(() => {
        creativesEndpointStub.createCandidate.and
            .returnValue(of(mockedCreativeCandidate, asapScheduler))
            .calls.reset();

        const mockedNewCandidate = clone(mockedCandidateCreateParams);
        service
            .createCandidate(
                mockedBatchId,
                mockedNewCandidate,
                requestStateUpdater
            )
            .subscribe(candidate => {
                expect(candidate).toEqual(mockedCreativeCandidate);
            });
        tick();

        expect(creativesEndpointStub.createCandidate).toHaveBeenCalledTimes(1);
        expect(creativesEndpointStub.createCandidate).toHaveBeenCalledWith(
            mockedBatchId,
            mockedNewCandidate,
            requestStateUpdater
        );
    }));

    it('should get creative candidate via endpoint', () => {
        creativesEndpointStub.getCandidate.and
            .returnValue(of(mockedCreativeCandidate, asapScheduler))
            .calls.reset();

        service
            .getCandidate(
                mockedBatchId,
                mockedCreativeCandidateId,
                requestStateUpdater
            )
            .subscribe(candidate => {
                expect(candidate).toEqual(mockedCreativeCandidate);
            });
        expect(creativesEndpointStub.getCandidate).toHaveBeenCalledTimes(1);
        expect(creativesEndpointStub.getCandidate).toHaveBeenCalledWith(
            mockedBatchId,
            mockedCreativeCandidateId,
            requestStateUpdater
        );
    });

    it('should edit creative candidate via endpoint', () => {
        creativesEndpointStub.editCandidate.and
            .returnValue(of(mockedCreativeCandidate, asapScheduler))
            .calls.reset();

        service
            .editCandidate(
                mockedBatchId,
                mockedCreativeCandidate,
                requestStateUpdater
            )
            .subscribe(newCandidate => {
                expect(newCandidate).toEqual(mockedCreativeCandidate);
            });

        expect(creativesEndpointStub.editCandidate).toHaveBeenCalledTimes(1);
        expect(creativesEndpointStub.editCandidate).toHaveBeenCalledWith(
            mockedBatchId,
            mockedCreativeCandidate,
            requestStateUpdater
        );
    });
});
