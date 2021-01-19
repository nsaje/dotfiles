import {
    FetchCreativesActionEffect,
    FetchCreativesAction,
} from './fetch-creatives.effect';
import {of, asapScheduler} from 'rxjs';
import {SetEntitiesAction} from '../reducers/set-entities.reducer';
import {fakeAsync, tick} from '@angular/core/testing';
import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {Creative} from '../../../../../../core/creatives/types/creative';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {AdType} from '../../../../../../app.constants';
import {
    TrackerEventType,
    TrackerMethod,
} from '../../../../../../core/creatives/creatives.constants';
import {CreativesStoreState} from '../creatives.store.state';
import {ScopeParams} from '../../../../../../shared/types/scope-params';
import {CreativesSearchParams} from '../../../types/creatives-search-params';
import {SetScopeAction} from '../reducers/set-scope.reducer';
import {PaginationState} from '../../../../../../shared/components/smart-grid/types/pagination-state';
import {SetAllEntitiesSelectedAction} from '../reducers/set-all-entities-selected.reducer';

describe('FetchCreativesActionEffect', () => {
    let creativesServiceStub: jasmine.SpyObj<CreativesService>;
    let mockedCreative: Creative;
    let effect: FetchCreativesActionEffect;
    let requestStateUpdater: RequestStateUpdater;

    beforeEach(() => {
        creativesServiceStub = jasmine.createSpyObj(CreativesService.name, [
            'list',
        ]);
        requestStateUpdater = (requestName, requestState) => {};

        effect = new FetchCreativesActionEffect(creativesServiceStub);
        mockedCreative = {
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
        };
    });

    it('should fetch creatives via service', fakeAsync(() => {
        const scope: ScopeParams = {agencyId: '65', accountId: '497'};
        const pagination: PaginationState = {page: 1, pageSize: 10};
        const searchParams: CreativesSearchParams = {
            keyword: 'test',
            creativeType: AdType.CONTENT,
            tags: ['a', 'b', 'c'],
        };

        spyOn(effect, 'dispatch').and.returnValue(Promise.resolve(true));

        creativesServiceStub.list.and
            .returnValue(of([mockedCreative], asapScheduler))
            .calls.reset();

        effect.effect(
            new CreativesStoreState(),
            new FetchCreativesAction({
                scope,
                pagination,
                searchParams,
                requestStateUpdater: requestStateUpdater,
            })
        );
        tick();

        expect(creativesServiceStub.list).toHaveBeenCalledTimes(1);
        expect(creativesServiceStub.list).toHaveBeenCalledWith(
            scope.agencyId,
            scope.accountId,
            0,
            pagination.pageSize,
            searchParams.keyword,
            searchParams.creativeType,
            searchParams.tags,
            requestStateUpdater
        );

        expect(effect.dispatch).toHaveBeenCalledTimes(3);
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetEntitiesAction([mockedCreative])
        );
        expect(effect.dispatch).toHaveBeenCalledWith(new SetScopeAction(scope));
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetAllEntitiesSelectedAction(false)
        );
    }));
});
