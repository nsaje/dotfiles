import './scope-selector-card.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    ContentChild,
    TemplateRef,
} from '@angular/core';

@Component({
    selector: 'zem-scope-selector-card',
    templateUrl: './scope-selector-card.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ScopeSelectorCardComponent<T> {
    @Input()
    scopeState: T;
    @Input()
    value: T;
    @Input()
    isDisabled: boolean;
    @Output()
    valueChange = new EventEmitter<T>();

    @ContentChild('scopeHeaderTemplate', {
        read: TemplateRef,
        static: false,
    })
    scopeHeaderTemplate: TemplateRef<any>;

    @ContentChild('scopeContentTemplate', {
        read: TemplateRef,
        static: false,
    })
    scopeContentTemplate: TemplateRef<any>;
}
