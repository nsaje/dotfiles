import {Injectable} from '@angular/core';
import {
    CanActivate,
    ActivatedRouteSnapshot,
    RouterStateSnapshot,
} from '@angular/router';
import {AuthStore} from '../core/auth/services/auth.store';

@Injectable()
export class CanActivateUserGuard implements CanActivate {
    constructor(private authStore: AuthStore) {}

    canActivate(
        route: ActivatedRouteSnapshot,
        state: RouterStateSnapshot
    ): Promise<boolean> {
        return this.authStore.initStore();
    }
}
