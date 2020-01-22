import {HttpErrorResponse} from '@angular/common/http';
import {RequestStateUpdater} from '../types/request-state-updater';
import * as commonHelpers from './common.helpers';
import * as deepmerge from 'deepmerge';
import deepClean from './deep-clean.helper';

export function getStoreRequestStateUpdater(
    store: any,
    requestsStateName: string = 'requests'
): RequestStateUpdater {
    return (requestName, requestState) => {
        store.setState({
            ...store.state,
            [requestsStateName]: {
                ...store.state[requestsStateName],
                [requestName]: {
                    ...store.state[requestsStateName][requestName],
                    ...requestState,
                },
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

export function getNewStateWithoutNull<T>(state: T): Partial<T> {
    const cleanedState = deepClean(state, {
        emptyArrays: false,
        emptyObjects: false,
        emptyStrings: false,
    });
    return cleanedState;
}
