import {Injectable} from '@angular/core';
import {AuthStore} from '../auth/services/auth.store';
import * as commonHelpers from '../../shared/helpers/common.helpers';
import {LOCAL_STORAGE_ROOT_KEY} from './local-storage.constants';

@Injectable()
export class LocalStorageService {
    constructor(private authStore: AuthStore) {}

    getItem(key: string, namespace: string = null): any | null {
        const storageKey = this.getStorageKey(key, namespace);
        const value: string = window.localStorage.getItem(storageKey);
        return commonHelpers.isDefined(value) ? JSON.parse(value) : null;
    }

    setItem(key: string, value: any, namespace: string = null): void {
        const storageKey = this.getStorageKey(key, namespace);
        window.localStorage.setItem(storageKey, JSON.stringify(value));
    }

    removeItem(key: string, namespace: string = null): void {
        const storageKey = this.getStorageKey(key, namespace);
        window.localStorage.removeItem(storageKey);
    }

    private getStorageKey(key: string, namespace: string = null): string {
        const userId: string = this.authStore.getCurrentUserId();
        return [
            LOCAL_STORAGE_ROOT_KEY,
            ...(commonHelpers.isDefined(userId) ? [userId] : []),
            ...(commonHelpers.isDefined(namespace) ? [namespace] : []),
            ...(commonHelpers.isDefined(key) ? [key] : []),
        ].join('.');
    }
}
