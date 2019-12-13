import {Component, Inject, OnInit} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import {EntityType} from '../../../../app.constants';
import {ENTITY_MANAGER_CONFIG} from '../../entity-manager.config';

@Component({
    selector: 'zem-entity-settings-router-outlet',
    templateUrl: './entity-settings.router-outlet.html',
})
// tslint:disable-next-line component-class-suffix
export class EntitySettingsRouterOutlet implements OnInit {
    readonly EntityType = EntityType;
    entityId: number = null;
    newEntityParentId: number = null;
    entityType: EntityType = null;

    constructor(
        @Inject('ajs$rootScope') private ajs$rootScope: any,
        @Inject('ajs$location') private ajs$location: any,
        @Inject('ajs$state') private ajs$state: any
    ) {}

    ngOnInit() {
        this.updateActiveSettingsEntity();
        this.ajs$rootScope.$on('$zemStateChangeSuccess', () => {
            this.updateActiveSettingsEntity();
        });
        this.ajs$rootScope.$on('$locationChangeSuccess', () => {
            this.updateActiveSettingsEntity();
        });
    }

    private updateActiveSettingsEntity() {
        this.entityId = null;
        this.newEntityParentId = null;
        this.entityType = null;

        if (
            this.ajs$state.includes('v2.analytics') &&
            this.isSettingsQueryParamSet()
        ) {
            this.entityId = this.getEntityIdFromUrlParams();
            this.entityType = this.getEntityTypeFromUrlParams();
        } else if (this.ajs$state.includes('v2.createEntity')) {
            this.newEntityParentId = this.getEntityIdFromUrlParams();
            this.entityType = this.getEntityTypeFromUrlParams();
        }
    }

    private isSettingsQueryParamSet(): boolean {
        return this.ajs$location.search()[
            ENTITY_MANAGER_CONFIG.settingsQueryParam
        ];
    }

    private getEntityIdFromUrlParams(): number {
        return (
            this.ajs$location.search()[ENTITY_MANAGER_CONFIG.idQueryParam] ||
            this.ajs$state.params[ENTITY_MANAGER_CONFIG.idStateParam]
        );
    }

    private getEntityTypeFromUrlParams(): EntityType {
        return (
            this.ajs$location.search()[ENTITY_MANAGER_CONFIG.levelQueryParam] ||
            ENTITY_MANAGER_CONFIG.levelToEntityTypeMap[
                this.ajs$state.params[ENTITY_MANAGER_CONFIG.levelStateParam]
            ]
        );
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemEntitySettingsRouterOutlet',
    downgradeComponent({
        component: EntitySettingsRouterOutlet,
        propagateDigest: false,
    })
);
