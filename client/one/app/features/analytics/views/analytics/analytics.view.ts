import './analytics.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    OnDestroy,
    Inject,
    HostBinding,
    ChangeDetectorRef,
} from '@angular/core';
import {downgradeComponent} from '@angular/upgrade/static';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {
    Breakdown,
    Level,
    LevelStateParam,
    BreakdownStateParam,
} from '../../../../app.constants';
import {
    DEFAULT_BREAKDOWN,
    LEVEL_STATE_PARAM_TO_LEVEL_MAP,
    BREAKDOWN_STATE_PARAM_TO_BREAKDOWN_MAP,
    LEVEL_TO_ENTITY_TYPE_MAP,
} from '../../analytics.config';

@Component({
    selector: 'zem-analytics-view',
    templateUrl: './analytics.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AnalyticsView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-analytics-view';

    level: Level;
    breakdown: Breakdown;
    chartBreakdown: Breakdown;
    entity: any;
    isInitialized: boolean = false;

    private stateChangeListener$: Function;

    constructor(
        private changeDetectorRef: ChangeDetectorRef,
        @Inject('ajs$rootScope') private ajs$rootScope: any,
        @Inject('ajs$state') private ajs$state: any,
        @Inject('zemPermissions') public zemPermissions: any,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {}

    ngOnInit(): void {
        this.updateInternalState();
        this.stateChangeListener$ = this.ajs$rootScope.$on(
            '$zemStateChangeSuccess',
            () => {
                this.updateInternalState();
            }
        );
    }

    ngOnDestroy(): void {
        if (commonHelpers.isDefined(this.stateChangeListener$)) {
            this.stateChangeListener$();
        }
    }

    updateInternalState() {
        this.level = this.getLevel(this.ajs$state.params.level);
        if (!commonHelpers.isDefined(this.level)) {
            this.isInitialized = false;
            this.changeDetectorRef.markForCheck();
            return;
        }

        this.breakdown = this.getBreakdown(
            this.level,
            this.ajs$state.params.breakdown
        );
        this.chartBreakdown = this.getChartBreakdown(
            this.level,
            this.breakdown
        );

        const entityId = this.ajs$state.params.id;
        if (!commonHelpers.isDefined(entityId)) {
            this.entity = null;
            this.isInitialized = true;
            this.changeDetectorRef.markForCheck();
            return;
        }

        this.zemNavigationNewService
            .getEntityById(LEVEL_TO_ENTITY_TYPE_MAP[this.level], entityId)
            .then((entity: any) => {
                this.entity = entity;
                this.isInitialized = true;
                this.changeDetectorRef.markForCheck();
            });
    }

    private getLevel(levelStateParam: LevelStateParam): Level {
        return LEVEL_STATE_PARAM_TO_LEVEL_MAP[levelStateParam];
    }

    private getBreakdown(
        level: Level,
        breakdownStateParam: BreakdownStateParam
    ): Breakdown {
        const breakdown =
            BREAKDOWN_STATE_PARAM_TO_BREAKDOWN_MAP[breakdownStateParam];
        if (
            commonHelpers.isDefined(breakdown) &&
            this.canSeeBreakdown(breakdown)
        ) {
            return breakdown;
        }
        return DEFAULT_BREAKDOWN[level];
    }

    private getChartBreakdown(level: Level, breakdown: Breakdown): Breakdown {
        return breakdown === Breakdown.INSIGHTS
            ? DEFAULT_BREAKDOWN[level]
            : breakdown;
    }

    private canSeeBreakdown(breakdown: Breakdown): boolean {
        const isDeliveryBreakdown = [
            Breakdown.COUNTRY,
            Breakdown.STATE,
            Breakdown.DMA,
            Breakdown.DEVICE,
            Breakdown.PLACEMENT,
            Breakdown.OPERATING_SYSTEM,
        ].includes(breakdown);
        if (isDeliveryBreakdown) {
            return this.zemPermissions.hasPermission(
                'zemauth.can_see_top_level_delivery_breakdowns'
            );
        }
        return true;
    }
}

declare var angular: angular.IAngularStatic;
angular.module('one.downgraded').directive(
    'zemAnalyticsView',
    downgradeComponent({
        component: AnalyticsView,
        propagateDigest: false,
    })
);
