import {asapScheduler, of} from 'rxjs';
import * as clone from 'clone';
import {tick, fakeAsync} from '@angular/core/testing';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {DealsEndpoint} from './deals.endpoint';
import {DealsService} from './deals.service';
import {Deal} from '../types/deal';

describe('DealsService', () => {
    let service: DealsService;
    let dealsEndpointStub: jasmine.SpyObj<DealsEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    let mockedDeal: Deal;
    let mockedDeals: Deal[];
    let mockedDealId: string;
    let mockedAgencyId: string;

    beforeEach(() => {
        dealsEndpointStub = jasmine.createSpyObj(DealsEndpoint.name, [
            'list',
            'create',
            'validate',
            'get',
            'edit',
        ]);
        service = new DealsService(dealsEndpointStub);
        requestStateUpdater = (requestName, requestState) => {};

        mockedAgencyId = '71';
        mockedDealId = '456346';
        mockedDeals = [
            {
                id: '10000000',
                dealId: '45345',
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
            {
                id: '10000001',
                dealId: '456346',
                description: 'second test deal',
                name: 'test deal number two',
                source: 'test2',
                floorPrice: '0.0007',
                createdDt: new Date(),
                modifiedDt: new Date(),
                createdBy: 'test@test.com',
                numOfAccounts: 0,
                numOfCampaigns: 0,
                numOfAdgroups: 0,
            },
            {
                id: '10000002',
                dealId: '345245',
                description: 'test 3',
                name: 'test deal 3',
                source: 'bsoutbrain',
                floorPrice: '0.0047',
                createdDt: new Date(),
                modifiedDt: new Date(),
                createdBy: 'test@test.com',
                numOfAccounts: 0,
                numOfCampaigns: 0,
                numOfAdgroups: 0,
            },
        ];
        mockedDeal = clone(mockedDeals[0]);
    });

    it('should get deals via endpoint', () => {
        const limit = 10;
        const offset = 0;
        dealsEndpointStub.list.and
            .returnValue(of(mockedDeals, asapScheduler))
            .calls.reset();

        service
            .list(mockedAgencyId, offset, limit, requestStateUpdater)
            .subscribe(deals => {
                expect(deals).toEqual(mockedDeals);
            });
        expect(dealsEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(dealsEndpointStub.list).toHaveBeenCalledWith(
            mockedAgencyId,
            offset,
            limit,
            requestStateUpdater
        );
    });

    it('should create new deal', fakeAsync(() => {
        dealsEndpointStub.create.and
            .returnValue(of(mockedDeal, asapScheduler))
            .calls.reset();

        const mockedNewDeal = clone(mockedDeal);
        mockedNewDeal.id = null;
        service
            .save(mockedAgencyId, mockedNewDeal, requestStateUpdater)
            .subscribe(deal => {
                expect(deal).toEqual(mockedDeal);
            });
        tick();

        expect(dealsEndpointStub.create).toHaveBeenCalledTimes(1);
        expect(dealsEndpointStub.create).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedNewDeal,
            requestStateUpdater
        );
    }));

    it('should get deal via endpoint', () => {
        dealsEndpointStub.get.and
            .returnValue(of(mockedDeal, asapScheduler))
            .calls.reset();

        service
            .get(mockedAgencyId, mockedDealId, requestStateUpdater)
            .subscribe(deal => {
                expect(deal).toEqual(mockedDeal);
            });
        expect(dealsEndpointStub.get).toHaveBeenCalledTimes(1);
        expect(dealsEndpointStub.get).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedDealId,
            requestStateUpdater
        );
    });

    it('should edit deal via endpoint', () => {
        const mockedNewDeal = clone(mockedDeals[0]);
        dealsEndpointStub.edit.and
            .returnValue(of(mockedDeal, asapScheduler))
            .calls.reset();

        service
            .save(mockedAgencyId, mockedNewDeal, requestStateUpdater)
            .subscribe(newDeal => {
                expect(newDeal).toEqual(mockedNewDeal);
            });

        expect(dealsEndpointStub.edit).toHaveBeenCalledTimes(1);
        expect(dealsEndpointStub.edit).toHaveBeenCalledWith(
            mockedAgencyId,
            mockedNewDeal,
            requestStateUpdater
        );
    });
});