import {AuthStore} from '../auth/services/auth.store';
import {LOCAL_STORAGE_ROOT_KEY} from './local-storage.constants';
import {LocalStorageService} from './local-storage.service';

describe('LocalStorageService', () => {
    let service: LocalStorageService;
    let authStoreStub: jasmine.SpyObj<AuthStore>;

    const userId = '12345';
    const key = 'key';
    const value: string[] = ['1', '2', '3', '4', '5'];
    const namespace = 'namespace';

    let store: any;
    let storageKey: string;

    beforeEach(() => {
        authStoreStub = jasmine.createSpyObj(AuthStore.name, [
            'getCurrentUserId',
        ]);
        authStoreStub.getCurrentUserId.and.callFake(() => userId);

        // @ts-ignore
        service = new LocalStorageService(authStoreStub);

        store = {};
        storageKey = `${LOCAL_STORAGE_ROOT_KEY}.${userId}.${namespace}.${key}`;
    });

    it('should correctly set item', () => {
        spyOn(localStorage, 'setItem').and.callFake(
            (key: string, value: string) => {
                store[key] = value;
            }
        );

        service.setItem(key, value, namespace);
        expect(localStorage.setItem).toHaveBeenCalledWith(
            storageKey,
            JSON.stringify(value)
        );
        expect(store[storageKey]).toEqual(JSON.stringify(value));
    });

    it('should correctly get item', () => {
        store[storageKey] = JSON.stringify(value);
        spyOn(localStorage, 'getItem').and.callFake((key: string) => {
            return store[key];
        });
        const result = service.getItem(key, namespace);
        expect(localStorage.getItem).toHaveBeenCalledWith(storageKey);
        expect(result).toEqual(value);
    });

    it('should correctly remove item', () => {
        store[storageKey] = JSON.stringify(value);
        spyOn(localStorage, 'removeItem').and.callFake((key: string) => {
            delete store[key];
        });
        service.removeItem(key, namespace);
        expect(localStorage.removeItem).toHaveBeenCalledWith(storageKey);
        expect(store).toEqual({});
    });
});
