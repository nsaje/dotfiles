import './list-group.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
} from '@angular/core';
import {ListGroupItem} from './types/list-group-item';

@Component({
    selector: 'zem-list-group',
    templateUrl: './list-group.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ListGroupComponent {
    @Input()
    items: ListGroupItem[];
    @Input()
    value: string;
    @Input()
    isIconVisible: boolean = true;
    @Input()
    isDisplayValueVisible: boolean = true;
    @Output()
    valueChange = new EventEmitter<string>();

    trackByIndex(index: number): string {
        return index.toString();
    }
}
