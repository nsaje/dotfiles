import './publisher-groups-library.view.less';

import {
    Component,
    ChangeDetectionStrategy,
    OnInit,
    Inject,
    HostBinding,
    ChangeDetectorRef,
    OnDestroy,
} from '@angular/core';
import {LevelParam, Level} from '../../../../app.constants';
import {
    LEVEL_PARAM_TO_LEVEL_MAP,
    LEVEL_TO_ENTITY_TYPE_MAP,
} from '../../../../app.constants';
import {ActivatedRoute, Params} from '@angular/router';
import {Subject} from 'rxjs';
import {takeUntil} from 'rxjs/operators';

@Component({
    selector: 'zem-publisher-groups-library-view',
    templateUrl: './publisher-groups-library.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PublisherGroupsLibraryView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-publisher-groups-library-view';

    account: any;
    agency: any;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        private route: ActivatedRoute,
        private changeDetectorRef: ChangeDetectorRef,
        @Inject('zemNavigationNewService') private zemNavigationNewService: any
    ) {}

    ngOnInit(): void {
        this.route.params
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe((params: Params) => {
                this.updateInternalState(
                    this.route.snapshot.data.level,
                    params.id
                );
            });
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    updateInternalState(levelParam: LevelParam, accountId: string) {
        const level = this.getLevel(levelParam);

        this.zemNavigationNewService
            .getEntityById(LEVEL_TO_ENTITY_TYPE_MAP[level], accountId)
            .then((account: any) => {
                this.account = account;
                this.changeDetectorRef.markForCheck();
            });
    }

    private getLevel(levelParam: LevelParam): Level {
        return LEVEL_PARAM_TO_LEVEL_MAP[levelParam];
    }
}
