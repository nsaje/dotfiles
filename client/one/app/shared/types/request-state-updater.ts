import {RequestState} from './request-state';

export type RequestStateUpdater = (
    requestName: string,
    requestState: RequestState
) => void;
