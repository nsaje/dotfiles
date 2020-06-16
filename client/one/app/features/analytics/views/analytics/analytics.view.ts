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
import * as commonHelpers from '../../../../shared/helpers/common.helpers';
import {
    Breakdown,
    Level,
    LevelParam,
    BreakdownParam,
} from '../../../../app.constants';
import {
    DEFAULT_BREAKDOWN,
    BREAKDOWN_PARAM_TO_BREAKDOWN_MAP,
} from '../../analytics.config';
import {
    LEVEL_PARAM_TO_LEVEL_MAP,
    LEVEL_TO_ENTITY_TYPE_MAP,
} from '../../../../app.constants';
import {ActivatedRoute, Params} from '@angular/router';
import {takeUntil} from 'rxjs/operators';
import {Subject} from 'rxjs';
import {AlertsStore} from '../../services/alerts-store/alerts.store';

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

    private ngUnsubscribe$: Subject<void> = new Subject();
    private dateRangeUpdateHandler: any;

    constructor(
        public alertsStore: AlertsStore,
        private route: ActivatedRoute,
        private changeDetectorRef: ChangeDetectorRef,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any,
        @Inject('zemDataFilterService') private zemDataFilterService: any
    ) {}

    ngOnInit(): void {
        this.route.params
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe((params: Params) => {
                this.updateInternalState(
                    this.route.snapshot.data.level,
                    params.id,
                    params.breakdown
                );
            });
        this.dateRangeUpdateHandler = this.zemDataFilterService.onDateRangeUpdate(
            () => {
                if (this.isInitialized) {
                    this.setAlerts();
                }
            }
        );
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
        if (commonHelpers.isDefined(this.dateRangeUpdateHandler)) {
            this.dateRangeUpdateHandler();
        }
    }

    updateInternalState(
        levelParam: LevelParam,
        entityId: string | null,
        breakdownParam: BreakdownParam | null
    ) {
        this.level = this.getLevel(levelParam);
        this.breakdown = this.getBreakdown(this.level, breakdownParam);
        this.chartBreakdown = this.getChartBreakdown(
            this.level,
            this.breakdown
        );

        if (!commonHelpers.isDefined(entityId)) {
            this.entity = null;
            this.isInitialized = true;
            this.setAlerts();
            this.changeDetectorRef.markForCheck();
            return;
        }

        this.zemNavigationNewService
            .getEntityById(LEVEL_TO_ENTITY_TYPE_MAP[this.level], entityId)
            .then((entity: any) => {
                if (
                    !commonHelpers.isDefined(this.entity) ||
                    this.entity.id !== entity.id
                ) {
                    this.entity = entity;
                }

                this.isInitialized = true;
                this.setAlerts();
                this.changeDetectorRef.markForCheck();
            });
    }

    setAlerts() {
        const dateRange = this.zemDataFilterService.getDateRange();
        this.alertsStore.setStore(
            this.level,
            commonHelpers.safeGet(this.entity, x => x.id),
            this.breakdown,
            commonHelpers.safeGet(dateRange, x => x.startDate),
            commonHelpers.safeGet(dateRange, x => x.endDate)
        );
    }

    private getLevel(levelParam: LevelParam): Level {
        return LEVEL_PARAM_TO_LEVEL_MAP[levelParam];
    }

    private getBreakdown(
        level: Level,
        breakdownParam: BreakdownParam | null
    ): Breakdown {
        const breakdown = BREAKDOWN_PARAM_TO_BREAKDOWN_MAP[breakdownParam];
        if (commonHelpers.isDefined(breakdown)) {
            return breakdown;
        }
        return DEFAULT_BREAKDOWN[level];
    }

    private getChartBreakdown(level: Level, breakdown: Breakdown): Breakdown {
        return breakdown === Breakdown.INSIGHTS
            ? DEFAULT_BREAKDOWN[level]
            : breakdown;
    }
}
