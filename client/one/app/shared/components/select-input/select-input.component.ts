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
} from '@angular/core';
import * as commonHelpers from '../../helpers/common.helpers';
import * as clone from 'clone';
import {NgSelectComponent} from '@ng-select/ng-select';

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
    hasError: boolean = false;
    @Output()
    valueChange = new EventEmitter<string>();

    @ViewChild('zemSelect', {static: false})
    zemSelect: NgSelectComponent;

    model: string;
    formattedItems: any[];

    private onWindowScrollCallback: any;

    constructor() {
        this.onWindowScrollCallback = this.onWindowScroll.bind(this);
    }

    ngOnInit(): void {
        window.addEventListener('scroll', this.onWindowScrollCallback, true);
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
        window.removeEventListener('scroll', this.onWindowScrollCallback, true);
    }

    onChange($event: any) {
        this.valueChange.emit($event ? $event[this.bindValue] : null);
    }

    onWindowScroll($event: any): void {
        if (
            !commonHelpers.isDefined(this.zemSelect) ||
            !this.zemSelect.isOpen
        ) {
            return;
        }
        const className = 'ng-dropdown-panel-items';
        if (($event.target.className as string).indexOf(className) > -1) {
            return;
        }
        this.zemSelect.close();
    }
}
