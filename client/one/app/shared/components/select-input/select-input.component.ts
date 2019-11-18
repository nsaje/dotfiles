import '@ng-select/ng-select/themes/default.theme.css';
import './select-input.component.less';

import {
    Component,
    OnChanges,
    ChangeDetectionStrategy,
    SimpleChanges,
    EventEmitter,
    Output,
    Input,
    OnDestroy,
    OnInit,
    ViewChild,
    TemplateRef,
    ContentChild,
} from '@angular/core';
import * as commonHelpers from '../../helpers/common.helpers';
import * as clone from 'clone';
import {NgSelectComponent} from '@ng-select/ng-select';
import {Subject} from 'rxjs';
import {debounceTime, distinctUntilChanged, takeUntil} from 'rxjs/operators';

@Component({
    selector: 'zem-select-input',
    templateUrl: './select-input.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class SelectInputComponent implements OnInit, OnChanges, OnDestroy {
    @Input()
    value: string;
    @Input()
    bindLabel: string;
    @Input()
    bindValue: string;
    @Input()
    appendTo: 'body';
    @Input()
    items: any[];
    @Input()
    placeholder: string;
    @Input()
    isDisabled: boolean = false;
    @Input()
    isSearchable: boolean = false;
    @Input()
    isClearable: boolean = true;
    @Input()
    groupByValue: string;
    @Input()
    orderByValue: string;
    @Input()
    closeOnSelect: boolean = true;
    @Input()
    clearSearchOnSelect: boolean = false;
    @Input()
    isLoading: boolean = false;
    @Input()
    searchFn: Function;
    @Input()
    dropdownPosition: 'bottom' | 'top' | 'auto' = 'auto';
    @Input()
    debounceTime: number;
    @Input()
    hasError: boolean = false;
    @Output()
    valueChange = new EventEmitter<string>();
    @Output()
    search = new EventEmitter<string>();

    private ngUnsubscribe$: Subject<void> = new Subject();
    private searchDebouncer$: Subject<string> = new Subject<string>();

    @ViewChild('zemSelect', {static: false})
    zemSelect: NgSelectComponent;

    @ContentChild('optionGroupTemplate', {read: TemplateRef, static: false})
    optionGroupTemplate: TemplateRef<any>;

    @ContentChild('optionTemplate', {read: TemplateRef, static: false})
    optionTemplate: TemplateRef<any>;

    model: string;
    formattedItems: any[];

    private onWindowScrollCallback: any;

    ngOnInit(): void {
        if (this.appendTo === 'body') {
            this.onWindowScrollCallback = this.onWindowScroll.bind(this);
            window.addEventListener(
                'scroll',
                this.onWindowScrollCallback,
                true
            );
        }
        this.searchDebouncer$
            .pipe(
                debounceTime(
                    commonHelpers.getValueOrDefault(this.debounceTime, 200)
                ),
                takeUntil(this.ngUnsubscribe$)
            )
            .subscribe(term => {
                this.search.emit(term);
            });
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.model = this.value;
        }
        if (changes.bindLabel) {
            this.bindLabel = commonHelpers.getValueOrDefault(
                this.bindLabel,
                ''
            );
        }
        if (changes.bindValue) {
            this.bindValue = commonHelpers.getValueOrDefault(
                this.bindValue,
                ''
            );
        }
        if (changes.items) {
            this.formattedItems = clone(
                commonHelpers.getValueOrDefault(this.items, [])
            );
            if (commonHelpers.isDefined(this.orderByValue)) {
                this.formattedItems.sort((a, b) => {
                    if (a[this.orderByValue] < b[this.orderByValue]) {
                        return -1;
                    }
                    if (a[this.orderByValue] > b[this.orderByValue]) {
                        return 1;
                    }
                    return 0;
                });
            }
        }
    }

    ngOnDestroy(): void {
        if (commonHelpers.isDefined(this.onWindowScrollCallback)) {
            window.removeEventListener(
                'scroll',
                this.onWindowScrollCallback,
                true
            );
        }
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onChange($event: any) {
        this.valueChange.emit($event ? $event[this.bindValue] : null);
        if (this.clearSearchOnSelect) {
            // TODO (msuber): remove handleClearClick workaround when
            // https://github.dyf62976.workers.dev/ng-select/ng-select/pull/1257
            // is resolved and merged to master.
            this.zemSelect.handleClearClick();
        }
    }

    onSearch($event: string) {
        this.searchDebouncer$.next($event);
    }

    onWindowScroll($event: any): void {
        if (
            !commonHelpers.isDefined(this.zemSelect) ||
            !this.zemSelect.isOpen
        ) {
            return;
        }
        const tagName = 'ng-dropdown';
        if (
            commonHelpers.isDefined($event.target.offsetParent) &&
            ($event.target.offsetParent.tagName as string)
                .toLowerCase()
                .indexOf(tagName) > -1
        ) {
            return;
        }
        this.zemSelect.close();
    }
}
