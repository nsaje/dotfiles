import {RequestState} from './request-state';

export class StoreEndpoint {
    setRequestState (store: any, requestName: string, requestState: RequestState): void {
        store.setState({
            ...store.state,
            requests: {
                ...store.state.requests,
                [requestName]: requestState,
            },
        });
    }
}
