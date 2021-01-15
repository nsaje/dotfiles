import './creatives-actions.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Input,
    OnChanges,
    OnInit,
    Output,
    SimpleChanges,
} from '@angular/core';
import {CreativesSearchParams} from '../../types/creatives-search-params';
import * as commonHelpers from '../../../../../shared/helpers/common.helpers';
import {Subject} from 'rxjs';
import {debounceTime, distinctUntilChanged, takeUntil} from 'rxjs/operators';
import {AdType} from '../../../../../app.constants';
import {CREATIVE_TYPES} from '../../creatives-shared.config';

@Component({
    selector: 'zem-creatives-actions',
    templateUrl: './creatives-actions.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreativesActionsComponent implements OnInit, OnChanges {
    @Input()
    searchParams: CreativesSearchParams;
    @Input()
    availableTags: string[];
    @Input()
    isDisabled: boolean = false;
    @Input()
    isReadOnly: boolean = true;
    @Output()
    searchParamsChange: EventEmitter<CreativesSearchParams> = new EventEmitter<
        CreativesSearchParams
    >();

    readonly creativeTypes: {id: AdType; name: string}[] = CREATIVE_TYPES;

    private ngUnsubscribe$: Subject<void> = new Subject();
    private keywordDebouncer$: Subject<string> = new Subject<string>();

    ngOnInit() {
        this.keywordDebouncer$
            .pipe(
                debounceTime(500),
                distinctUntilChanged(),
                takeUntil(this.ngUnsubscribe$)
            )
            .subscribe($event => {
                this.emitNewSearchParams({keyword: $event});
            });
    }

    ngOnChanges(changes: SimpleChanges): void {}

    onKeywordChange($event: string) {
        const keyword: string | null = commonHelpers.isNotEmpty($event)
            ? $event
            : null;
        this.keywordDebouncer$.next(keyword);
    }

    onCreativeTypeChange($event: AdType) {
        this.emitNewSearchParams({creativeType: $event});
    }

    onTagsChange($event: string[]) {
        this.emitNewSearchParams({tags: $event});
    }

    private emitNewSearchParams(changes: Partial<CreativesSearchParams>) {
        this.searchParamsChange.emit({...this.searchParams, ...changes});
    }
}
