import './tag-picker.component.less';

import {
    ChangeDetectionStrategy,
    Component,
    EventEmitter,
    Input,
    OnChanges,
    OnDestroy,
    OnInit,
    Output,
    ViewChild,
} from '@angular/core';
import {SelectInputComponent} from '../select-input/select-input.component';
import {isNotEmpty} from '../../helpers/common.helpers';
import {Subject} from 'rxjs';
import {debounceTime, distinctUntilChanged, takeUntil} from 'rxjs/operators';

@Component({
    selector: 'zem-tag-picker',
    templateUrl: './tag-picker.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TagPickerComponent implements OnInit, OnChanges, OnDestroy {
    @Input()
    value: string[];
    @Input()
    items: string[];
    @Input()
    placeholder: string = 'Add tags';
    @Input()
    canCreateTags: boolean = false;
    @Input()
    appendTo: 'body';
    @Input()
    isDisabled: boolean = false;
    @Input()
    isLoading: boolean = false;
    @Input()
    hasError: boolean = false;
    @Input()
    debounceTime: number = 200;
    @Output()
    valueChange: EventEmitter<string[]> = new EventEmitter<string[]>();
    @Output()
    search: EventEmitter<string> = new EventEmitter<string>();

    @ViewChild(SelectInputComponent, {static: false})
    selectInput: SelectInputComponent;

    private ngUnsubscribe$: Subject<void> = new Subject();
    private searchDebouncer$: Subject<string> = new Subject<string>();

    formattedItems: {tag: string}[] = [];
    searchText: string = '';

    ngOnInit(): void {
        this.searchDebouncer$
            .pipe(
                debounceTime(this.debounceTime),
                distinctUntilChanged(),
                takeUntil(this.ngUnsubscribe$)
            )
            .subscribe(term => {
                this.search.emit(term);
            });
    }

    ngOnChanges() {
        this.formattedItems = (this.items || []).map(item => ({
            tag: item,
        }));
    }

    ngOnDestroy(): void {
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
    }

    onSearch($event: string) {
        this.searchText = $event;
        this.searchDebouncer$.next($event);
    }

    onKeyEnter() {
        if (isNotEmpty(this.searchText) && !this.existingTagsMatchSearch()) {
            this.valueChange.emit(this.value.concat([this.searchText]));
            this.selectInput.zemSelect.close();
        }
    }

    private existingTagsMatchSearch(): boolean {
        return this.items.some(tag =>
            tag.toUpperCase().includes(this.searchText.toUpperCase())
        );
    }
}
