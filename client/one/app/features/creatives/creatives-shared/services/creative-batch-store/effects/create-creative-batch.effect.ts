import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {Injectable} from '@angular/core';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {takeUntil} from 'rxjs/operators';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {CreativeBatch} from '../../../../../../core/creatives/types/creative-batch';
import {SetEntityAction} from '../reducers/set-entity.reducer';
import {ScopeParams} from '../../../../../../shared/types/scope-params';

export interface CreateCreativeBatchParams {
    scope: ScopeParams;
    requestStateUpdater: RequestStateUpdater;
}

export class CreateCreativeBatchAction extends StoreAction<
    CreateCreativeBatchParams
> {}

// tslint:disable-next-line: max-classes-per-file
@Injectable()
export class CreateCreativeBatchActionEffect extends StoreEffect<
    CreativeBatchStoreState,
    CreateCreativeBatchAction
> {
    constructor(private service: CreativesService) {
        super();
    }

    effect(
        state: CreativeBatchStoreState,
        action: CreateCreativeBatchAction
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            const params: CreateCreativeBatchParams = action.payload;
            const newBatch: CreativeBatch = {
                name: '',
                accountId: params.scope.accountId,
                agencyId: params.scope.agencyId,
            };
            this.service
                .createBatch(newBatch, params.requestStateUpdater)
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