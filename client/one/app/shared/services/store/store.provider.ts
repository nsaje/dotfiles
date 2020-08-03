import {StoreAction} from './store.action';
import {StoreReducer} from './store.reducer';
import {StoreEffect} from './store.effect';
import {Type} from '@angular/core';

interface Provider<
    T1 extends StoreAction<any>,
    T2 extends StoreReducer<any, any> | StoreEffect<any, any>
> {
    provide: Type<T1>;
    useClass: Type<T2>;
}

export abstract class StoreProvider<
    T1 extends StoreAction<any>,
    T2 extends StoreReducer<any, any> | StoreEffect<any, any>
> implements Provider<T1, T2> {
    provide: Type<T1>;
    useClass: Type<T2>;
}
