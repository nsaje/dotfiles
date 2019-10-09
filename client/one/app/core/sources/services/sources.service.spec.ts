import {asapScheduler, of} from 'rxjs';
import * as clone from 'clone';
import {tick, fakeAsync} from '@angular/core/testing';
import {RequestStateUpdater} from '../../../shared/types/request-state-updater';
import {SourcesEndpoint} from './sources.endpoint';
import {SourcesService} from './sources.service';
import {Source} from '../types/source';

describe('SourcesService', () => {
    let service: SourcesService;
    let sourcesEndpointStub: jasmine.SpyObj<SourcesEndpoint>;
    let requestStateUpdater: RequestStateUpdater;

    let mockedSources: Source[];
    let mockedAgencyId: string;

    beforeEach(() => {
        sourcesEndpointStub = jasmine.createSpyObj(SourcesEndpoint.name, [
            'list',
        ]);
        service = new SourcesService(sourcesEndpointStub);
        requestStateUpdater = (requestName, requestState) => {};

        mockedAgencyId = '71';
        mockedSources = [
            {
                slug: 'slug-1',
                name: 'Source 1',
                released: true,
                deprecated: false,
            },
            {
                slug: 'slug-2',
                name: 'Source 2',
                released: false,
                deprecated: false,
            },
            {
                slug: 'slug-3',
                name: 'Source 3',
                released: true,
                deprecated: true,
            },
        ];
    });

    it('should get sources via endpoint', () => {
        sourcesEndpointStub.list.and
            .returnValue(of(mockedSources, asapScheduler))
            .calls.reset();

        service.list(mockedAgencyId, requestStateUpdater).subscribe(sources => {
            expect(sources).toEqual(mockedSources);
        });
        expect(sourcesEndpointStub.list).toHaveBeenCalledTimes(1);
        expect(sourcesEndpointStub.list).toHaveBeenCalledWith(
            mockedAgencyId,
            requestStateUpdater
        );
    });
});
