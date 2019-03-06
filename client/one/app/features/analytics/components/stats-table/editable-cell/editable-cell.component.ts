import './editable-cell.component.less';
import {
    Component,
    Input,
    OnChanges,
    ChangeDetectionStrategy,
    SimpleChanges,
    ComponentFactoryResolver,
    Injector,
    ApplicationRef,
    Inject,
    AfterViewInit,
    ViewChild,
    ElementRef,
    Renderer2,
    Output,
    EventEmitter,
    OnInit,
    OnDestroy,
    ChangeDetectorRef,
} from '@angular/core';
import {CdkPortal, DomPortalHost} from '@angular/cdk/portal';
import {DOCUMENT} from '@angular/platform-browser';
import {EditableCellMode} from './editable-cell.constants';
import {KeyCode} from '../../../../../app.constants';

// TODO (msuber): handle editMessage in popover component
@Component({
    selector: 'zem-editable-cell',
    templateUrl: './editable-cell.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class EditableCellComponent
    implements OnInit, OnChanges, AfterViewInit, OnDestroy {
    @Input()
    isEditable: boolean;
    @Input()
    editMessage: string;
    @Input()
    mode: EditableCellMode;
    @Input()
    containerElement: HTMLElement;
    @Output()
    modeChange = new EventEmitter<EditableCellMode>();

    @ViewChild(CdkPortal)
    portal: CdkPortal;
    @ViewChild('portalContent')
    portalContentElementRef: ElementRef;

    shouldRenderAsModal: boolean = false;
    hostElementOffsetTop: number;
    hostElementOffsetLeft: number;

    private portalHost: DomPortalHost;

    private onWindowScrollCallback: any;
    private onKeydownCallback: any;
    private onWindowResizeCallback: any;
    private onContainerElementScrollCallback: any;

    constructor(
        @Inject(DOCUMENT) private document: Document,
        private componentFactoryResolver: ComponentFactoryResolver,
        private applicationRef: ApplicationRef,
        private injector: Injector,
        private hostElement: ElementRef,
        private renderer: Renderer2,
        private changeDetectorRef: ChangeDetectorRef,
        @Inject('ajs$rootScope') private ajs$rootScope: any
    ) {
        this.onWindowScrollCallback = this.switchToReadMode.bind(this);
        this.onKeydownCallback = this.onKeydown.bind(this);
        this.onWindowResizeCallback = this.switchToReadMode.bind(this);
        this.onContainerElementScrollCallback = this.switchToReadMode.bind(
            this
        );
    }

    ngOnInit(): void {
        this.ajs$rootScope.$on('$zemStateChangeSuccess', () => {
            this.modeChange.emit(EditableCellMode.READ);
        });
    }

    ngOnChanges(changes: SimpleChanges): void {
        if (changes.mode && this.portalHost) {
            switch (this.mode) {
                case EditableCellMode.EDIT:
                    this.attachHost();
                    break;
                case EditableCellMode.READ:
                    this.detachHost();
                    break;
            }
        }
    }

    ngAfterViewInit(): void {
        this.portalHost = new DomPortalHost(
            this.document.body,
            this.componentFactoryResolver,
            this.applicationRef,
            this.injector
        );
    }

    ngOnDestroy(): void {
        this.detachHost();
    }

    switchToEditMode(): void {
        if (!this.isEditable) {
            return;
        }
        this.modeChange.emit(EditableCellMode.EDIT);
    }

    switchToReadMode(): void {
        this.modeChange.emit(EditableCellMode.READ);
    }

    private attachHost(): void {
        const hostElementOffset = this.getElementOffset(
            this.hostElement,
            this.document
        );

        this.shouldRenderAsModal = false;
        this.hostElementOffsetTop = hostElementOffset.topOffset;
        this.hostElementOffsetLeft = hostElementOffset.leftOffset;
        this.portalHost.attach(this.portal);

        window.addEventListener('scroll', this.onWindowScrollCallback);
        window.addEventListener('keydown', this.onKeydownCallback);
        window.addEventListener('resize', this.onWindowResizeCallback);
        this.containerElement.addEventListener(
            'scroll',
            this.onContainerElementScrollCallback
        );

        setTimeout(() => {
            this.shouldRenderAsModal = this.isPortalContentOverflowingContainer(
                this.hostElementOffsetLeft,
                this.portalContentElementRef,
                this.containerElement
            );
            if (this.shouldRenderAsModal) {
                this.renderer.addClass(this.document.body, 'modal-open');
                this.changeDetectorRef.detectChanges();
            }
        });
    }

    private detachHost(): void {
        if (this.portalHost.hasAttached()) {
            this.portalHost.detach();

            window.removeEventListener('scroll', this.onWindowScrollCallback);
            window.removeEventListener('keydown', this.onKeydownCallback);
            window.removeEventListener('resize', this.onWindowResizeCallback);
            this.containerElement.removeEventListener(
                'scroll',
                this.onContainerElementScrollCallback
            );
            this.renderer.removeClass(this.document.body, 'modal-open');
        }
    }

    private getElementOffset(
        element: ElementRef,
        document: Document
    ): {
        topOffset: number;
        leftOffset: number;
    } {
        const hostElementRect = element.nativeElement.getBoundingClientRect();
        const scrollTop =
            window.pageYOffset || document.documentElement.scrollTop;
        const scrollLeft =
            window.pageXOffset || document.documentElement.scrollLeft;
        return {
            topOffset: (hostElementRect.top as number) + scrollTop,
            leftOffset: (hostElementRect.left as number) + scrollLeft,
        };
    }

    private isPortalContentOverflowingContainer(
        hostElementOffsetLeft: number,
        portalContentElementRef: ElementRef,
        containerElement: HTMLElement
    ): boolean {
        const portalContentElementWidth: number =
            portalContentElementRef.nativeElement.clientWidth;
        const containerElementOffsetLeft = containerElement.getBoundingClientRect()
            .left;
        const containerElementWidth = containerElement.getBoundingClientRect()
            .width;

        const overflow =
            hostElementOffsetLeft +
            portalContentElementWidth -
            (containerElementOffsetLeft + containerElementWidth);
        return overflow > 0;
    }

    private onKeydown($event: KeyboardEvent): void {
        if ($event.keyCode === KeyCode.ESCAPE) {
            this.switchToReadMode();
        }
    }
}
