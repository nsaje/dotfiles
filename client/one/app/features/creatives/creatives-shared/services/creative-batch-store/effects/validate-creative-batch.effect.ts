import {StoreAction} from '../../../../../../shared/services/store/store.action';
import {Injectable} from '@angular/core';
import {StoreEffect} from '../../../../../../shared/services/store/store.effect';
import {CreativeBatchStoreState} from '../creative-batch.store.state';
import {CreativesService} from '../../../../../../core/creatives/services/creatives.service';
import {RequestStateUpdater} from '../../../../../../shared/types/request-state-updater';
import {takeUntil} from 'rxjs/operators';
import {HttpErrorResponse} from '@angular/common/http';
import * as storeHelpers from '../../../../../../shared/helpers/store.helpers';
import {SetFieldsErrorsAction} from '../reducers/set-fields-errors.reducer';
import {CreativeBatchStoreFieldsErrorsState} from '../creative-batch.store.fields-errors-state';

export interface ValidateCreativeBatchParams {
    requestStateUpdater: RequestStateUpdater;
}

export class ValidateCreativeBatchAction extends StoreAction<
    ValidateCreativeBatchParams
> {}

// tslint:disable-next-line: max-classes-per-file
@Injectable()
export class ValidateCreativeBatchActionEffect extends StoreEffect<
    CreativeBatchStoreState,
    ValidateCreativeBatchAction
> {
    constructor(private service: CreativesService) {
        super();
    }

    effect(
        state: CreativeBatchStoreState,
        action: ValidateCreativeBatchAction
    ): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            const params: ValidateCreativeBatchParams = action.payload;
            this.service
                .validateBatch(state.entity, params.requestStateUpdater)
                .pipe(takeUntil(this.ngUnsubscribe$))
                .subscribe(
                    () => {
                        this.dispatch(
                            new SetFieldsErrorsAction(
                                new CreativeBatchStoreFieldsErrorsState()
                            )
                        );
                    },
                    (error: HttpErrorResponse) => {
                        const fieldsErrors = storeHelpers.getStoreFieldsErrorsState(
                            new CreativeBatchStoreFieldsErrorsState(),
                            error
                        );
                        this.dispatch(new SetFieldsErrorsAction(fieldsErrors));
                    }
                );
        });
    }
}
