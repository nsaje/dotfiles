import {Directive, Output, EventEmitter, OnDestroy, ElementRef, ChangeDetectorRef} from '@angular/core';

const KEY_ESC = 27;

@Directive({
    selector: '[zemDropdown]',
    exportAs: 'zemDropdown',
})
export class DropdownDirective implements OnDestroy {
    @Output() onOpen = new EventEmitter();
    @Output() onClose = new EventEmitter();

    element: HTMLElement;
    private closeOnOutsideClickHandler: (event: MouseEvent) => void;
    private closeOnEscapeKeyHandler: (event: KeyboardEvent) => void;

    constructor (private elementRef: ElementRef, private changeDetectorRef: ChangeDetectorRef) {
        this.element = this.elementRef.nativeElement;
    }

    ngOnDestroy () {
        this.close();
    }

    open (): void {
        document.addEventListener('click', this.closeOnOutsideClickHandler = this.closeOnOutsideClick.bind(this), true);
        document.addEventListener(
            'keydown', this.closeOnEscapeKeyHandler = this.closeOnEscapeKey.bind(this), true
        );
        this.element.classList.add('zem-dropdown--open');
        this.positionContent();
        this.onOpen.emit(undefined);
    }

    close (): void {
        document.removeEventListener('click', this.closeOnOutsideClickHandler, true);
        document.removeEventListener('keydown', this.closeOnEscapeKeyHandler, true);
        this.element.classList.remove('zem-dropdown--open', 'zem-dropdown--reversed');
        this.onClose.emit(undefined);
    }

    isOpen (): boolean {
        return this.element.classList.contains('zem-dropdown--open');
    }

    private closeOnOutsideClick (event: MouseEvent): void {
        if (!this.element.contains(<Element> event.target)) {
            event.preventDefault();
            event.stopPropagation();
            this.close();
            this.changeDetectorRef.detectChanges();
        }
    }

    private closeOnEscapeKey (event: KeyboardEvent): void {
        if (event.keyCode === KEY_ESC) {
            event.preventDefault();
            event.stopPropagation();
            this.close();
            this.changeDetectorRef.detectChanges();
        }
    }

    private positionContent (): void {
        const contentElement = this.element.querySelector('.zem-dropdown__content');
        const contentLeft = contentElement.getBoundingClientRect().left;
        const contentWidth = contentElement.clientWidth;
        const windowWidth = window.innerWidth;

        if (contentLeft + contentWidth > windowWidth) {
            this.element.classList.add('zem-dropdown--reversed');
        }
    }
}
