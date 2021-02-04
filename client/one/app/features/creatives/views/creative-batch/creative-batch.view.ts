import './creative-batch.view.less';

import {Component, HostBinding, OnDestroy, OnInit} from '@angular/core';
import {Subject} from 'rxjs';
import {ActivatedRoute, Params} from '@angular/router';
import {takeUntil} from 'rxjs/operators';

@Component({
    selector: 'zem-creative-batch-view',
    templateUrl: './creative-batch.view.html',
})
export class CreativeBatchView implements OnInit, OnDestroy {
    @HostBinding('class')
    cssClass = 'zem-creative-batch-view';

    batchId: string | null = null;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(private route: ActivatedRoute) {}

    ngOnInit() {
        this.route.params
            .pipe(takeUntil(this.ngUnsubscribe$))
            .subscribe(params => {
                this.updateInternalState(params);
            });
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    private updateInternalState(params: Params) {
        this.batchId = params.batchId;
    }
}
