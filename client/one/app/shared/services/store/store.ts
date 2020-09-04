import {Store as ObservableStore} from 'rxjs-observable-store';
import {StoreProvider} from './store.provider';
import {StoreReducer} from './store.reducer';
import {StoreAction} from './store.action';
import {Injector, OnDestroy, Injectable} from '@angular/core';
import {StoreEffect} from './store.effect';
import * as commonHelpers from '../../helpers/common.helpers';
import * as arrayHelpers from '../../helpers/array.helpers';

@Injectable()
export abstract class Store<T extends {}> extends ObservableStore<T>
    implements OnDestroy {
    private reducers: {
        actionName: string;
        instance: StoreReducer<T, StoreAction<any>>;
    }[] = [];

    private effects: {
        actionName: string;
        instance: StoreEffect<T, StoreAction<any>>;
    }[] = [];

    constructor(initialState: T, private injector: Injector) {
        super(initialState);
        const providers = this.provide();
        this.effects = this.getEffects(providers);
        this.reducers = this.getReducers(providers);
    }

    abstract provide(): StoreProvider<
        StoreAction<any>,
        StoreReducer<T, StoreAction<any>> | StoreEffect<T, StoreAction<any>>
    >[];

    async dispatch<T>(action: StoreAction<T>): Promise<boolean> {
        const reducer = this.getReducerForAction(action);
        if (commonHelpers.isDefined(reducer)) {
            this.setState(reducer.reduce({...this.state}, action));
            return true;
        }
        const effect = this.getEffectForAction(action);
        if (commonHelpers.isDefined(effect)) {
            return await effect.effect({...this.state}, action);
        }
        throw new Error(
            `Missing Reducer or Effect for action (${action.constructor.name})!`
        );
    }

    ngOnDestroy(): void {
        this.destroyEffects();
    }

    private getEffects(
        providers: StoreProvider<
            StoreAction<any>,
            StoreReducer<T, StoreAction<any>> | StoreEffect<T, StoreAction<any>>
        >[]
    ): {
        actionName: string;
        instance: StoreEffect<T, StoreAction<any>>;
    }[] {
        return providers
            .filter(provider => {
                return provider.useClass.prototype instanceof StoreEffect;
            })
            .map(effect => {
                const instance = this.injector.get(
                    effect.useClass
                ) as StoreEffect<T, StoreAction<any>>;
                instance.dispatch = instance.dispatch.bind(this);
                return {
                    actionName: effect.provide.name,
                    instance: instance,
                };
            });
    }

    private getReducers(
        providers: StoreProvider<
            StoreAction<any>,
            StoreReducer<T, StoreAction<any>> | StoreEffect<T, StoreAction<any>>
        >[]
    ): {
        actionName: string;
        instance: StoreReducer<T, StoreAction<any>>;
    }[] {
        return providers
            .filter(provider => {
                return provider.useClass.prototype instanceof StoreReducer;
            })
            .map(reducer => {
                const instance = new reducer.useClass() as StoreReducer<
                    T,
                    StoreAction<any>
                >;
                return {
                    actionName: reducer.provide.name,
                    instance: instance,
                };
            });
    }

    private getReducerForAction<T>(
        action: StoreAction<T>
    ): StoreReducer<any, any> {
        const reducer = this.reducers.find(
            r => r.actionName === action.constructor.name
        );
        return commonHelpers.isDefined(reducer) ? reducer.instance : null;
    }

    private getEffectForAction<T>(
        action: StoreAction<T>
    ): StoreEffect<any, any> {
        const effect = this.effects.find(
            e => e.actionName === action.constructor.name
        );
        return commonHelpers.isDefined(effect) ? effect.instance : null;
    }

    private destroyEffects(): void {
        if (arrayHelpers.isEmpty(this.effects)) {
            return;
        }
        this.effects.forEach(effect => {
            effect.instance.ngOnDestroy();
        });
    }
}
