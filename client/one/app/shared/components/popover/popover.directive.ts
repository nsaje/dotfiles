import './popover.directive.less';

import {
    Directive,
    Input,
    TemplateRef,
    OnInit,
    ViewContainerRef,
    ComponentFactoryResolver,
    ComponentRef,
    ElementRef,
    OnChanges,
    SimpleChanges,
    Renderer2,
    Injector,
    NgZone,
    Inject,
    SimpleChange,
    OnDestroy,
    ChangeDetectorRef,
} from '@angular/core';
import {NgbPopover, NgbPopoverConfig} from '@ng-bootstrap/ng-bootstrap';
import {NgbPopoverWindow} from '@ng-bootstrap/ng-bootstrap/popover/popover';
import {DOCUMENT} from '@angular/platform-browser';
import * as commonHelpers from '../../helpers/common.helpers';

@Directive({
    selector: '[zemPopover]',
})
export class PopoverDirective extends NgbPopover
    implements OnInit, OnChanges, OnDestroy {
    @Input()
    zemPopover: string | TemplateRef<any>;
    @Input()
    stayOpenOnHover: boolean = false;

    private canClosePopover: boolean = true;

    private triggerElementMouseoverListener: Function;
    private triggerElementMouseoutListener: Function;
    private popoverElementMouseoverListener: Function;
    private popoverElementMouseoutListener: Function;

    constructor(
        private elementRef: ElementRef,
        private renderer: Renderer2,
        injector: Injector,
        componentFactoryResolver: ComponentFactoryResolver,
        viewContainerRef: ViewContainerRef,
        config: NgbPopoverConfig,
        ngZone: NgZone,
        @Inject(DOCUMENT) document: Document,
        changeDetectorRef: ChangeDetectorRef
    ) {
        super(
            elementRef,
            renderer,
            injector,
            componentFactoryResolver,
            viewContainerRef,
            config,
            ngZone,
            document,
            changeDetectorRef
        );
    }

    ngOnInit(): void {
        this.ngbPopover = this.zemPopover;
        this.popoverClass = 'zem-popover';
        super.ngOnInit();

        if (this.stayOpenOnHover && this.elementRef) {
            this.triggerElementMouseoverListener = this.renderer.listen(
                this.elementRef.nativeElement,
                'mouseover',
                () => {
                    this.canClosePopover = false;
                }
            );

            this.triggerElementMouseoutListener = this.renderer.listen(
                this.elementRef.nativeElement,
                'mouseout',
                () => {
                    this.canClosePopover = true;
                    this.close();
                }
            );
        }
    }

    ngOnChanges(changes: SimpleChanges) {
        if (changes.zemPopover) {
            changes.ngbPopover = new SimpleChange(
                this.ngbPopover,
                this.zemPopover,
                false
            );
        }
        super.ngOnChanges(changes);
    }

    ngOnDestroy() {
        this.removeEventListener(this.triggerElementMouseoverListener);
        this.removeEventListener(this.triggerElementMouseoutListener);
        this.removeEventListener(this.popoverElementMouseoverListener);
        this.removeEventListener(this.popoverElementMouseoutListener);
        super.ngOnDestroy();
    }

    open() {
        super.open();
        if (this.stayOpenOnHover && (this as any)._windowRef) {
            // In TS you can not access private properies of the base class
            // without getting compiler errors. The next implementation allows
            // us to overcome this restriction. If NgbPopover gets upgraded
            // check if the _windowRef is still used.
            const popoverElement: HTMLElement = ((this as any)
                ._windowRef as ComponentRef<NgbPopoverWindow>).location
                .nativeElement;

            this.removeEventListener(this.popoverElementMouseoverListener);
            this.popoverElementMouseoverListener = this.renderer.listen(
                popoverElement,
                'mouseover',
                () => {
                    this.canClosePopover = false;
                }
            );

            this.removeEventListener(this.popoverElementMouseoutListener);
            this.popoverElementMouseoutListener = this.renderer.listen(
                popoverElement,
                'mouseout',
                () => {
                    this.canClosePopover = true;
                    this.close();
                }
            );
        }
    }

    close() {
        // The setTimeout is used in order to
        // allow possible listeners to change the
        // value of canClosePopover property.
        setTimeout(() => {
            if (this.canClosePopover) {
                super.close();
            }
        }, 0);
    }

    private removeEventListener(eventListener: Function): void {
        if (commonHelpers.isDefined(eventListener)) {
            eventListener();
        }
    }
}
