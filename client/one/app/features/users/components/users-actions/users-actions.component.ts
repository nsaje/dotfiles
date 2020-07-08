import './users-actions.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    OnInit,
    OnDestroy,
} from '@angular/core';
import {Subject} from 'rxjs';
import {takeUntil, distinctUntilChanged, debounceTime} from 'rxjs/operators';
import * as commonHelpers from '../../../../shared/helpers/common.helpers';

@Component({
    selector: 'zem-users-actions',
    templateUrl: './users-actions.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class UsersActionsComponent implements OnInit, OnDestroy {
    @Input()
    value: string;
    @Input()
    isDisabled: boolean = false;
    @Output()
    search = new EventEmitter<string>();
    @Output()
    userCreate = new EventEmitter<void>();

    private ngUnsubscribe$: Subject<void> = new Subject();
    private searchDebouncer$: Subject<string> = new Subject<string>();

    ngOnInit() {
        this.searchDebouncer$
            .pipe(
                debounceTime(500),
                distinctUntilChanged(),
                takeUntil(this.ngUnsubscribe$)
            )
            .subscribe($event => {
                this.search.emit($event);
            });
    }

    ngOnDestroy() {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onSearchChange($event: string) {
        if (commonHelpers.isNotEmpty($event)) {
            this.searchDebouncer$.next($event);
        } else {
            this.searchDebouncer$.next(null);
        }
    }
}
