import {
    FetchCreativeTagsActionEffect,
    FetchCreativeTagsAction,
} from './fetch-creative-tags.effect';
import {of, asapScheduler} from 'rxjs';
import {SetCreativeTagsAction} from '../reducers/set-creative-tags.reducer';
import {fakeAsync, tick} from '@angular/core/testing';
import {CreativeTagsService} from '../../../../../../core/creative-tags/services/creative-tags.service';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {CreativesStoreState} from '../creatives.store.state';
import {ScopeParams} from '../../../../../../shared/types/scope-params';
import {CreativeTagsSearchParams} from '../../../types/creative-tags-search-params';
import {PaginationState} from '../../../../../../shared/components/smart-grid/types/pagination-state';

describe('FetchCreativeTagsActionEffect', () => {
    let creativesServiceStub: jasmine.SpyObj<CreativeTagsService>;
    let mockedCreativeTags: string[];
    let effect: FetchCreativeTagsActionEffect;
    let requestStateUpdater: RequestStateUpdater;

    beforeEach(() => {
        creativesServiceStub = jasmine.createSpyObj(CreativeTagsService.name, [
            'list',
        ]);
        requestStateUpdater = (requestName, requestState) => {};

        effect = new FetchCreativeTagsActionEffect(creativesServiceStub);
        mockedCreativeTags = ['abc', 'cde', 'def'];
    });

    it('should fetch creatives via service', fakeAsync(() => {
        const scope: ScopeParams = {agencyId: '65', accountId: '497'};
        const pagination: PaginationState = {page: 1, pageSize: 10};
        const searchParams: CreativeTagsSearchParams = {
            keyword: 'test',
        };

        spyOn(effect, 'dispatch').and.returnValue(Promise.resolve(true));

        creativesServiceStub.list.and
            .returnValue(of(mockedCreativeTags, asapScheduler))
            .calls.reset();

        effect.effect(
            new CreativesStoreState(),
            new FetchCreativeTagsAction({
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
            requestStateUpdater
        );

        expect(effect.dispatch).toHaveBeenCalledTimes(1);
        expect(effect.dispatch).toHaveBeenCalledWith(
            new SetCreativeTagsAction(mockedCreativeTags)
        );
    }));
});
