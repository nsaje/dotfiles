import './date-input.component.less';

import {
    Component,
    OnChanges,
    ChangeDetectionStrategy,
    SimpleChanges,
    EventEmitter,
    Output,
    Input,
    ViewChild,
    OnDestroy,
    OnInit,
} from '@angular/core';
import {
    NgbDate,
    NgbDateParserFormatter,
    NgbInputDatepicker,
} from '@ng-bootstrap/ng-bootstrap';
import {DateInputFormatter} from './date-input.formatter';
import * as commonHelpers from '../../helpers/common.helpers';

@Component({
    selector: 'zem-date-input',
    templateUrl: './date-input.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
    providers: [
        {provide: NgbDateParserFormatter, useClass: DateInputFormatter},
    ],
})
export class DateInputComponent implements OnInit, OnChanges, OnDestroy {
    @Input()
    value: Date;
    @Input('minDate')
    originalMinDate: Date;
    @Input('maxDate')
    originalMaxDate: Date;
    @Input()
    appendTo: 'body';
    @Input()
    isDisabled: boolean = false;
    @Input()
    isFocused: boolean = false;
    @Input()
    hasError: boolean = false;
    @Output()
    valueChange = new EventEmitter<Date>();

    @ViewChild('zemDatepicker', {static: false})
    zemDatepicker: NgbInputDatepicker;

    minDate: NgbDate;
    maxDate: NgbDate;
    model: NgbDate;

    private onWindowScrollCallback: any;

    constructor() {
        this.onWindowScrollCallback = this.onWindowScroll.bind(this);
    }

    ngOnInit(): void {
        window.addEventListener('scroll', this.onWindowScrollCallback, true);
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.model = this.convertFromDateToNgbDate(this.value);
        }
        if (changes.originalMinDate) {
            this.minDate = this.convertFromDateToNgbDate(this.originalMinDate);
        }
        if (changes.originalMaxDate) {
            this.maxDate = this.convertFromDateToNgbDate(this.originalMaxDate);
        }
    }

    ngOnDestroy(): void {
        window.removeEventListener('scroll', this.onWindowScrollCallback, true);
    }

    onDateSelect($event: NgbDate) {
        this.valueChange.emit(this.convertFromNgbDateToDate($event));
    }

    onWindowScroll($event: any): void {
        if (
            !commonHelpers.isDefined(this.zemDatepicker) ||
            !this.zemDatepicker.isOpen()
        ) {
            return;
        }
        this.zemDatepicker.close();
    }

    private convertFromDateToNgbDate(value: Date): NgbDate {
        if (commonHelpers.isDefined(value)) {
            // JavaScript counts months from 0 to 11
            // Convert Date format to NgbDateStruct
            // https://github.com/ng-bootstrap/ng-bootstrap/issues/839
            const month = value.getMonth() + 1;
            return new NgbDate(value.getFullYear(), month, value.getDate());
        }
        return null;
    }

    private convertFromNgbDateToDate(value: NgbDate): Date {
        if (commonHelpers.isDefined(value)) {
            // JavaScript counts months from 0 to 11
            // Convert Date format to NgbDateStruct
            // https://github.com/ng-bootstrap/ng-bootstrap/issues/839
            const month = value.month - 1;
            return new Date(value.year, month, value.day);
        }
        return null;
    }
}
