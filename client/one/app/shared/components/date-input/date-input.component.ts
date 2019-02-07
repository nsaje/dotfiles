import './date-input.component.less';

import {
    Component,
    OnChanges,
    ChangeDetectionStrategy,
    SimpleChanges,
    EventEmitter,
    Output,
    Input,
    OnInit,
} from '@angular/core';
import {NgbDate, NgbDateParserFormatter} from '@ng-bootstrap/ng-bootstrap';
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
export class DateInputComponent implements OnInit, OnChanges {
    @Input()
    value: Date;
    @Input('minDate')
    originalMinDate: Date;
    @Input()
    isDisabled: boolean;
    @Input()
    hasError: boolean;
    @Output()
    valueChange = new EventEmitter<Date>();

    minDate: NgbDate;
    model: NgbDate;

    ngOnInit(): void {
        this.minDate = this.fromDateToNgbDate(this.originalMinDate);
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.value) {
            this.model = this.fromDateToNgbDate(this.value);
        }
    }

    onDateSelect($event: NgbDate) {
        this.valueChange.emit(this.fromNgbDateToDate($event));
    }

    private fromDateToNgbDate(value: Date): NgbDate {
        if (commonHelpers.isDefined(value)) {
            // JavaScript counts months from 0 to 11
            // Convert Date format to NgbDateStruct
            // https://github.com/ng-bootstrap/ng-bootstrap/issues/839
            const month = value.getMonth() + 1;
            return new NgbDate(value.getFullYear(), month, value.getDate());
        }
        return null;
    }

    private fromNgbDateToDate(value: NgbDate): Date {
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