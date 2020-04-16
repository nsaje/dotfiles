import {
    ActivatedRouteSnapshot,
    RouteReuseStrategy,
    DetachedRouteHandle,
    RouterStateSnapshot,
} from '@angular/router';
import * as commonHelpers from '../shared/helpers/common.helpers';
import {RoutePathName} from '../app.constants';
import {ComponentRef} from '@angular/core';

const ROUTE_CACHE_TTL_MINUTES = 4;
const MAX_ROUTE_CACHE_MAP_SIZE = 4;

interface RouteCache {
    routeHandle: DetachedRouteHandle;
    expireDate: Date;
}

export class CacheRouteReuseStrategy implements RouteReuseStrategy {
    private routesToCache: string[] = [
        // `${RoutePathName.APP_BASE}/${RoutePathName.ANALYTICS}`,
        // `${RoutePathName.APP_BASE}/${RoutePathName.CREDITS}`,
        // `${RoutePathName.APP_BASE}/${RoutePathName.PIXELS_LIBRARY}`,
        // `${RoutePathName.APP_BASE}/${RoutePathName.REPORTS_LIBRARY}`,
        // `${RoutePathName.APP_BASE}/${RoutePathName.USERS_LIBRARY}`,
        // `${RoutePathName.APP_BASE}/${RoutePathName.INVENTORY_PLANNING}`,
    ];
    private routeCacheMap = new Map<string, RouteCache>();

    shouldDetach(route: ActivatedRouteSnapshot): boolean {
        const routePath = this.getRoutePath(route);
        const isRouteToCache = this.routesToCache.some(routeToCache => {
            return routePath.includes(routeToCache);
        });
        return isRouteToCache;
    }

    store(route: ActivatedRouteSnapshot, handle: DetachedRouteHandle): void {
        if (commonHelpers.isDefined(handle)) {
            const routePath = this.getRoutePath(route);
            if (this.routeCacheMap.has(routePath)) {
                if (this.hasRouteExpired(routePath)) {
                    const routeCache = this.routeCacheMap.get(routePath);
                    this.deactivateOutlet(routeCache.routeHandle);
                    this.routeCacheMap.delete(routePath);
                }
            } else {
                if (this.routeCacheMap.size >= MAX_ROUTE_CACHE_MAP_SIZE) {
                    const routePathToDelete: string = this.getRoutePathToDelete();
                    const routeCacheToDelete = this.routeCacheMap.get(
                        routePathToDelete
                    );
                    this.deactivateOutlet(routeCacheToDelete.routeHandle);
                    this.routeCacheMap.delete(routePathToDelete);
                }

                this.routeCacheMap.set(routePath, {
                    routeHandle: handle,
                    expireDate: this.getNewExpireDate(),
                });
            }
        }
    }

    shouldAttach(route: ActivatedRouteSnapshot): boolean {
        const routePath = this.getRoutePath(route);
        const isRouteToCache = this.routesToCache.some(routeToCache => {
            return routePath.includes(routeToCache);
        });
        const hasRouteExpired = this.hasRouteExpired(routePath);
        return (
            isRouteToCache &&
            !hasRouteExpired &&
            this.routeCacheMap.has(routePath)
        );
    }

    retrieve(route: ActivatedRouteSnapshot): DetachedRouteHandle {
        const routePath = this.getRoutePath(route);
        const routeCache = this.routeCacheMap.get(routePath);
        if (commonHelpers.isDefined(routeCache)) {
            return routeCache.routeHandle;
        }
        return null;
    }

    shouldReuseRoute(
        future: ActivatedRouteSnapshot,
        current: ActivatedRouteSnapshot
    ): boolean {
        const shouldReuseRoute = future.routeConfig === current.routeConfig;
        return shouldReuseRoute || current.data.reuseComponent;
    }

    private getRoutePath(route: ActivatedRouteSnapshot): string {
        let routePath = '';
        if (
            !commonHelpers.isDefined(route.firstChild) &&
            route.outlet === 'primary'
        ) {
            routePath = (<RouterStateSnapshot>(<any>route)._routerState).url;
        }
        return routePath;
    }

    private getNewExpireDate(): Date {
        const expireDate = new Date();
        expireDate.setMinutes(
            expireDate.getMinutes() + ROUTE_CACHE_TTL_MINUTES
        );
        return expireDate;
    }

    private hasRouteExpired(routePath: string): boolean {
        const routeCache = this.routeCacheMap.get(routePath);
        if (!commonHelpers.isDefined(routeCache)) {
            return true;
        }
        return routeCache.expireDate.getTime() < new Date().getTime();
    }

    private getRoutePathToDelete(): string {
        let routePath: string = null;
        let routeCache: RouteCache = null;
        Array.from(this.routeCacheMap).forEach(([key, value]) => {
            if (!commonHelpers.isDefined(routePath)) {
                routePath = key;
                routeCache = value;
                return;
            }
            if (value.expireDate.getTime() < routeCache.expireDate.getTime()) {
                routePath = key;
                routeCache = value;
            }
        });
        return routePath;
    }

    // If a snapshot is detached from the routing and re-attached later, there should be no memory leak.
    // But if a snapshot is detached from the routing and never re-attached to the router,
    // we need to take care about the memory management.
    private deactivateOutlet(handle: DetachedRouteHandle): void {
        const componentRef: ComponentRef<any> = (<any>handle).componentRef;
        if (commonHelpers.isDefined(componentRef)) {
            componentRef.destroy();
        }
    }
}
