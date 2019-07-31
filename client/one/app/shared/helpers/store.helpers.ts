import {HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../types/request-state-updater';
import * as commonHelpers from './common.helpers';
import * as deepmerge from 'deepmerge';

export function getStoreRequestStateUpdater(store: any): RequestStateUpdater {
    return (requestName, requestState) => {
        store.setState({
            ...store.state,
            requests: {
                ...store.state.requests,
                [requestName]: requestState,
            },
        });
    };
}

// TODO (jurebajt): Extend to work with field errors in string[][] format
export function getStoreFieldsErrorsState<T>(
    initialFieldsErrorsState: T,
    errorResponse: Partial<HttpErrorResponse> = {}
): T {
    if (
        !commonHelpers.isDefined(errorResponse.error) ||
        !commonHelpers.isDefined(errorResponse.error.details)
    ) {
        return initialFieldsErrorsState;
    }
    return deepmerge(initialFieldsErrorsState, errorResponse.error.details);
}
