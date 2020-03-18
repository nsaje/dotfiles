import './scope-selector.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    Output,
    EventEmitter,
    ContentChild,
    TemplateRef,
    OnChanges,
    SimpleChanges,
} from '@angular/core';
import {ScopeSelectorState} from './scope-selector.constants';
import {FieldErrors} from '../../types/field-errors';

@Component({
    selector: 'zem-scope-selector',
    templateUrl: './scope-selector.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ScopeSelectorComponent implements OnChanges {
    @Input()
    scopeState: ScopeSelectorState;
    @Input()
    isAgencyScopeDisabled: boolean;
    @Input()
    isAccountScopeDisabled: boolean;
    @Input()
    agencyErrors: FieldErrors = [];
    @Input()
    accountErrors: FieldErrors = [];
    @Output()
    scopeStateChange = new EventEmitter<ScopeSelectorState>();

    ScopeSelectorState = ScopeSelectorState;
    errors: FieldErrors = [];

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

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.accountErrors || changes.agencyErrors) {
            this.errors = (this.agencyErrors || []).concat(
                this.accountErrors || []
            );
        }
    }
}
