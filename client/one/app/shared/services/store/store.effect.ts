import {StoreAction} from './store.action';
import {RequestStateUpdater} from '../../types/request-state-updater';
import {OnDestroy, Injectable} from '@angular/core';
import {Subject} from 'rxjs';

interface Effect<
    T1,
    T2 extends StoreAction<{requestStateUpdater: RequestStateUpdater}>
> {
    effect(state: T1, action: T2): Promise<boolean>;
    dispatch<T>(action: StoreAction<T>): Promise<boolean>;
}

@Injectable()
export abstract class StoreEffect<
    T1 extends {},
    T2 extends StoreAction<{requestStateUpdater: RequestStateUpdater}>
> implements Effect<T1, T2>, OnDestroy {
    ngUnsubscribe$: Subject<void> = new Subject();

    abstract async effect(state: T1, action: T2): Promise<boolean>;

    async dispatch<T>(action: StoreAction<T>): Promise<boolean> {
        /**
         * In runtime 'this' refers to Store.
         */
        return await this.dispatch(action);
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }
}
