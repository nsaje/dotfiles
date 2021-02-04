import './tag-form-group.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Output,
    Input,
} from '@angular/core';

@Component({
    selector: 'zem-tag-form-group',
    templateUrl: './tag-form-group.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class TagFormGroupComponent {
    @Input()
    label: string;
    @Input()
    helpMessage: string;
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
    debounceTime: number = 200;
    @Input()
    errors: string[];
    @Output()
    valueChange: EventEmitter<string[]> = new EventEmitter<string[]>();
    @Output()
    search: EventEmitter<string> = new EventEmitter<string>();
}
