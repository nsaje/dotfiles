import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {Injectable} from '@angular/core';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {CreativesStoreState} from '../creatives.store.state';
import {takeUntil} from 'rxjs/operators';
import {Creative} from '../../../../../../core/creatives/types/creative';
import {SetEntitiesAction} from '../reducers/set-entities.reducer';
import {getOffset} from '../../../../../../shared/helpers/pagination.helper';
import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {SetScopeAction} from '../reducers/set-scope.reducer';
import {ScopeParams} from '../../../../../../shared/types/scope-params';
import {CreativesSearchParams} from '../../../types/creatives-search-params';
import {PaginationState} from '../../../../../../shared/components/smart-grid/types/pagination-state';
import {SetAllEntitiesSelectedAction} from '../reducers/set-all-entities-selected.reducer';

export interface FetchCreativesParams {
    scope: ScopeParams;
    pagination: PaginationState;
    searchParams: CreativesSearchParams;
    requestStateUpdater: RequestStateUpdater;
}

export class FetchCreativesAction extends StoreAction<FetchCreativesParams> {}

// tslint:disable-next-line: max-classes-per-file
@Injectable()
export class FetchCreativesActionEffect extends StoreEffect<
    CreativesStoreState,
    FetchCreativesAction
> {
    constructor(private service: CreativesService) {
        super();
    }

    effect(
        state: CreativesStoreState,
        action: FetchCreativesAction
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            const params: FetchCreativesParams = action.payload;
            const offset: number = getOffset(
                params.pagination.page,
                params.pagination.pageSize
            );
            this.service
                .list(
                    params.scope.agencyId,
                    params.scope.accountId,
                    offset,
                    params.pagination.pageSize,
                    params.searchParams.keyword,
                    params.searchParams.creativeType,
                    params.searchParams.tags,
                    params.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (creatives: Creative[]) => {
                        this.dispatch(new SetEntitiesAction(creatives));
                        this.dispatch(new SetScopeAction(params.scope));
                        this.dispatch(new SetAllEntitiesSelectedAction(false));
                        resolve(true);
                    },
                    () => {
                        resolve(false);
                    }
                );
        });
    }
}
