import './drawer.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    HostBinding,
    Output,
    EventEmitter,
} from '@angular/core';

@Component({
    selector: 'zem-drawer',
    templateUrl: './drawer.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DrawerComponent {
    @Input()
    @HostBinding('class.zem-drawer--open')
    isOpen: boolean;
    @Input()
    isClosable: boolean;
    @Output()
    closeRequest = new EventEmitter<undefined>();

    close() {
        if (this.isClosable) {
            this.closeRequest.emit();
        }
    }
}
