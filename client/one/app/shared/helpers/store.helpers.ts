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

export function getStoreFieldsErrorsState<T>(
    initialFieldsErrorsState: T,
    errorResponse: Partial<HttpErrorResponse> = {}
): T {
    if (
        !isBadRequestHttpStatusCode(errorResponse.status) ||
        !commonHelpers.isDefined(errorResponse.error) ||
        !commonHelpers.isDefined(errorResponse.error.details)
    ) {
        return initialFieldsErrorsState;
    }
    return deepmerge(initialFieldsErrorsState, errorResponse.error.details);
}

function isBadRequestHttpStatusCode(httpStatus: number): boolean {
    return commonHelpers.isDefined(httpStatus) && httpStatus === 400;
}

export function getNewStateWithoutNull<T>(state: T): Partial<T> {
    const cleanedState = deepClean(state, {
        emptyArrays: false,
        emptyObjects: false,
        emptyStrings: false,
    });
    return cleanedState;
}
