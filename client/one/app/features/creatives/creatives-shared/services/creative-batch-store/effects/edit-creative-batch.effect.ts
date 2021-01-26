import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {Injectable} from '@angular/core';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {takeUntil} from 'rxjs/operators';
import {CreativeBatch} from '../../../../../../core/creatives/types/creative-batch';
import {SetEntityAction} from '../reducers/set-entity.reducer';

export interface EditCreativeBatchParams {
    requestStateUpdater: RequestStateUpdater;
}

export class EditCreativeBatchAction extends StoreAction<
    EditCreativeBatchParams
> {}

// tslint:disable-next-line: max-classes-per-file
@Injectable()
export class EditCreativeBatchActionEffect extends StoreEffect<
    CreativeBatchStoreState,
    EditCreativeBatchAction
> {
    constructor(private service: CreativesService) {
        super();
    }

    effect(
        state: CreativeBatchStoreState,
        action: EditCreativeBatchAction
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            const params: EditCreativeBatchParams = action.payload;
            this.service
                .editBatch(state.entity, params.requestStateUpdater)
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
