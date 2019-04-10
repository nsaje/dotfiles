import './modal.component.less';

import {
    Component,
    Output,
    EventEmitter,
    ElementRef,
    ChangeDetectorRef,
    Input,
} from '@angular/core';

const KEY_ESC = 27;

@Component({
    selector: 'zem-modal',
    templateUrl: './modal.component.html',
})
export class ModalComponent {
    @Input()
    canCloseOnBackdropClick: boolean = true;
    @Input()
    canCloseOnEscapeKey: boolean = true;
    @Output()
    onClose = new EventEmitter<undefined>();

    isOpen = false;
    element: HTMLElement;
    private closeOnEscapeKeyHandler: (event: KeyboardEvent) => void;

    constructor(
        private elementRef: ElementRef,
        private changeDetectorRef: ChangeDetectorRef
    ) {
        this.element = this.elementRef.nativeElement;
    }

    open(): void {
        this.isOpen = true;
        document.body.classList.add('body--modal-open');
        document.addEventListener(
            'keydown',
            (this.closeOnEscapeKeyHandler = this.closeOnEscapeKey.bind(this)),
            true
        );
    }

    close(): void {
        this.isOpen = false;
        document.body.classList.remove('body--modal-open');
        document.removeEventListener(
            'keydown',
            this.closeOnEscapeKeyHandler,
            true
        );
        this.onClose.emit(undefined);
    }

    closeOnBackdropClick(event: MouseEvent): void {
        const backdropElement = this.element.querySelector(
            '.zem-modal__backdrop'
        );
        if (
            <Element>event.target === backdropElement &&
            this.canCloseOnBackdropClick
        ) {
            event.preventDefault();
            event.stopPropagation();
            this.close();
        }
    }

    private closeOnEscapeKey(event: KeyboardEvent): void {
        if (event.keyCode === KEY_ESC && this.canCloseOnEscapeKey) {
            event.preventDefault();
            event.stopPropagation();
            this.close();
            this.changeDetectorRef.detectChanges();
        }
    }
}
