import {StoreAction} from './store.action';

interface Reducer<T1, T2 extends StoreAction<any>> {
    reduce(state: T1, action: T2): T1;
}

export abstract class StoreReducer<T1, T2 extends StoreAction<any>>
    implements Reducer<T1, T2> {
    abstract reduce(state: T1, action: T2): T1;
}
