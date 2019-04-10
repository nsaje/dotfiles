import './drawer.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    Input,
    HostBinding,
    Output,
    EventEmitter,
    OnChanges,
    SimpleChanges,
} from '@angular/core';

@Component({
    selector: 'zem-drawer',
    templateUrl: './drawer.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DrawerComponent implements OnChanges {
    @Input()
    @HostBinding('class.zem-drawer--open')
    isOpen: boolean;
    @Input()
    isClosable: boolean;
    @Output()
    closeRequest = new EventEmitter<undefined>();

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.isOpen) {
            if (this.isOpen) {
                document.body.classList.add('body--drawer-open');
            } else {
                document.body.classList.remove('body--drawer-open');
            }
        }
    }

    close() {
        if (this.isClosable) {
            this.closeRequest.emit();
        }
    }
}
