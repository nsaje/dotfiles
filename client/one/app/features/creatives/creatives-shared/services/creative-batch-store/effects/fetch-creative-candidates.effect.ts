import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {Injectable} from '@angular/core';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {takeUntil} from 'rxjs/operators';
import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {CreativeCandidate} from '../../../../../../core/creatives/types/creative-candidate';
import {SetCandidatesAction} from '../reducers/set-candidates.reducer';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {getOffset} from '../../../../../../shared/helpers/pagination.helper';
import {PaginationState} from '../../../../../../shared/components/smart-grid/types/pagination-state';

export interface FetchCreativeCandidatesParams {
    batchId: string;
    pagination: PaginationState;
    requestStateUpdater: RequestStateUpdater;
}

export class FetchCreativeCandidatesAction extends StoreAction<
    FetchCreativeCandidatesParams
> {}

// tslint:disable-next-line: max-classes-per-file
@Injectable()
export class FetchCreativeCandidatesActionEffect extends StoreEffect<
    CreativeBatchStoreState,
    FetchCreativeCandidatesAction
> {
    constructor(private service: CreativesService) {
        super();
    }

    effect(
        state: CreativeBatchStoreState,
        action: FetchCreativeCandidatesAction
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            const params: FetchCreativeCandidatesParams = action.payload;
            const offset: number = getOffset(
                params.pagination.page,
                params.pagination.pageSize
            );
            this.service
                .listCandidates(
                    params.batchId,
                    offset,
                    params.pagination.pageSize,
                    params.requestStateUpdater
                )
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (creativeCandidates: CreativeCandidate[]) => {
                        this.dispatch(
                            new SetCandidatesAction(creativeCandidates)
                        );
                        resolve(true);
                    },
                    () => {
                        resolve(false);
                    }
                );
        });
    }
}
