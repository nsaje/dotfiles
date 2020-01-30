import './scope-selector.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    ContentChild,
    TemplateRef,
} from '@angular/core';
import {ScopeSelectorState} from './scope-selector.constants';

@Component({
    selector: 'zem-scope-selector',
    templateUrl: './scope-selector.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ScopeSelectorComponent {
    @Input()
    scopeState: ScopeSelectorState;
    @Input()
    isAgencyScopeDisabled: boolean;
    @Input()
    isAccountScopeDisabled: boolean;
    @Output()
    scopeStateChange = new EventEmitter<ScopeSelectorState>();

    ScopeSelectorState = ScopeSelectorState;

    @ContentChild('agencyScopeHeaderTemplate', {
        read: TemplateRef,
        static: false,
    })
    agencyScopeHeaderTemplate: TemplateRef<any>;

    @ContentChild('agencyScopeContentTemplate', {
        read: TemplateRef,
        static: false,
    })
    agencyScopeContentTemplate: TemplateRef<any>;

    @ContentChild('accountScopeHeaderTemplate', {
        read: TemplateRef,
        static: false,
    })
    accountScopeHeaderTemplate: TemplateRef<any>;

    @ContentChild('accountScopeContentTemplate', {
        read: TemplateRef,
        static: false,
    })
    accountScopeContentTemplate: TemplateRef<any>;
}
