import './pagination.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';

@Component({
    selector: 'zem-pagination',
    templateUrl: './pagination.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PaginationComponent {
    @Input()
    count: number;
    @Input()
    page: number;
    @Input()
    pageSize: number;
    @Input()
    maxSize: number = 5;
    @Input()
    rotate: boolean = true;
    @Input()
    boundaryLinks: boolean = true;
    @Output()
    pageChange = new EventEmitter<number>();

    onPageChange(page: number) {
        this.pageChange.emit(page);
    }
}
