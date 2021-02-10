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
import {AdType, CreativeBatchType} from '../../../../../app.constants';
import {CREATIVE_TYPES} from '../../creatives-shared.config';
import {MultiStepMenuOption} from '../../../../../shared/components/multi-step-menu/types/multi-step-menu-option';

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
    isLoadingTags: boolean = false;
    @Input()
    isDisabled: boolean = false;
    @Input()
    isReadOnly: boolean = true;
    @Output()
    searchParamsChange: EventEmitter<CreativesSearchParams> = new EventEmitter<
        CreativesSearchParams
    >();
    @Output()
    tagSearch: EventEmitter<string> = new EventEmitter<string>();
    @Output()
    batchCreate: EventEmitter<CreativeBatchType> = new EventEmitter<
        CreativeBatchType
    >();

    readonly creativeTypes: {id: AdType; name: string}[] = CREATIVE_TYPES;

    private ngUnsubscribe$: Subject<void> = new Subject();
    private keywordDebouncer$: Subject<string> = new Subject<string>();

    readonly addCreativeOptions: MultiStepMenuOption[] = [
        {
            name: 'One by one',
            description: 'Add ads one by one. You can add multiple ads.',
            nextOptions: [
                {
                    name: 'Native',
                    handler: () =>
                        this.batchCreate.emit(CreativeBatchType.NATIVE),
                },
                {
                    name: 'Video',
                    handler: () =>
                        this.batchCreate.emit(CreativeBatchType.VIDEO),
                },
                {
                    name: 'Display',
                    handler: () =>
                        this.batchCreate.emit(CreativeBatchType.DISPLAY),
                },
            ],
        },
    ];

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
        this.tagSearch.emit('');
    }

    private emitNewSearchParams(changes: Partial<CreativesSearchParams>) {
        this.searchParamsChange.emit({...this.searchParams, ...changes});
    }
}
