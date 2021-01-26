import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {Injectable} from '@angular/core';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {takeUntil} from 'rxjs/operators';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {CreativeBatch} from '../../../../../../core/creatives/types/creative-batch';
import {SetEntityAction} from '../reducers/set-entity.reducer';

export interface FetchCreativeBatchParams {
    batchId: string;
    requestStateUpdater: RequestStateUpdater;
}

export class FetchCreativeBatchAction extends StoreAction<
    FetchCreativeBatchParams
> {}

// tslint:disable-next-line: max-classes-per-file
@Injectable()
export class FetchCreativeBatchActionEffect extends StoreEffect<
    CreativeBatchStoreState,
    FetchCreativeBatchAction
> {
    constructor(private service: CreativesService) {
        super();
    }

    effect(
        state: CreativeBatchStoreState,
        action: FetchCreativeBatchAction
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            const params: FetchCreativeBatchParams = action.payload;
            this.service
                .getBatch(params.batchId, params.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    (creativeBatch: CreativeBatch) => {
                        this.dispatch(new SetEntityAction(creativeBatch));
                        resolve(true);
                    },
                    () => {
                        resolve(false);
                    }
                );
        });
    }
}
