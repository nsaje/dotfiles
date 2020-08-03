// tslint:disable: max-classes-per-file

import {Store} from './store';
import {StoreProvider} from './store.provider';
import {StoreAction} from './store.action';
import {StoreReducer} from './store.reducer';
import {StoreEffect} from './store.effect';
import {Injector} from '@angular/core';
import {fakeAsync, tick} from '@angular/core/testing';
import {RequestStateUpdater} from '../../types/request-state-updater';

describe('Store', () => {
    let service: TestService;
    let injectorStub: jasmine.SpyObj<Injector>;
    let store: TestStore;

    beforeEach(() => {
        service = new TestService();
        injectorStub = jasmine.createSpyObj(Injector.name, ['get']);
        injectorStub.get.and.returnValue(new FetchTestActionEffect(service));
        store = new TestStore(new TestStoreState(), injectorStub);
    });

    it('should be correctly initialized', () => {
        expect(store.state.test).toEqual('');
    });

    it('should correctly dispatch reducer actions', fakeAsync(() => {
        const value = 'reducer';
        expect(store.state.test).toEqual('');
        store.dispatch(new SetTestAction({test: value}));
        tick();
        expect(store.state.test).toEqual(value);
    }));

    it('should correctly dispatch effect actions', fakeAsync(() => {
        const value = 'effect';
        service.setResponse(value);
        expect(store.state.test).toEqual('');
        store.dispatch(new FetchTestAction({requestStateUpdater: null}));
        tick();
        expect(store.state.test).toEqual(value);
    }));

    it('should correctly throw error for missing reducer or effect', () => {
        const action = new MissingReducerOrEffectAction();
        store.dispatch(action).catch((error: Error) => {
            expect(error.message).toEqual(
                `Missing Reducer or Effect for action (${action.constructor.name})!`
            );
        });
    });
});

class TestService {
    response: string;

    setResponse(response: string): void {
        this.response = response;
    }

    fetch(): Promise<string> {
        return new Promise<string>(resolve => {
            resolve(this.response);
        });
    }
}

class TestStoreState {
    test: string = '';
}

class SetTestAction extends StoreAction<{test: string}> {}

class SetTestActionReducer extends StoreReducer<TestStoreState, SetTestAction> {
    reduce(state: TestStoreState, action: SetTestAction): TestStoreState {
        return {
            ...state,
            test: action.payload.test,
        };
    }
}

class FetchTestAction extends StoreAction<{
    requestStateUpdater: RequestStateUpdater;
}> {}

class FetchTestActionEffect extends StoreEffect<
    TestStoreState,
    FetchTestAction
> {
    constructor(private service: TestService) {
        super();
    }

    effect(state: TestStoreState, action: FetchTestAction): Promise<boolean> {
        return new Promise<boolean>(resolve => {
            this.service.fetch().then(data => {
                this.dispatch(new SetTestAction({test: data}));
            });
        });
    }
}

class MissingReducerOrEffectAction extends StoreAction<void> {}

class TestStore extends Store<TestStoreState> {
    provide(): StoreProvider<
        StoreAction<any>,
        | StoreReducer<TestStoreState, StoreAction<any>>
        | StoreEffect<TestStoreState, StoreAction<any>>
    >[] {
        return [
            {
                provide: SetTestAction,
                useClass: SetTestActionReducer,
            },
            {
                provide: FetchTestAction,
                useClass: FetchTestActionEffect,
            },
        ];
    }
}
