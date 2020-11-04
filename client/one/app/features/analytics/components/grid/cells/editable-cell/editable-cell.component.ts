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
    HostBinding,
} from '@angular/core';
import {CdkPortal, DomPortalHost} from '@angular/cdk/portal';
import {DOCUMENT} from '@angular/common';
import {
    EditableCellMode,
    EditableCellPlacement,
} from './editable-cell.constants';
import {
    KeyCode,
    RESIZE_OBSERVER_DEBOUNCE_TIME,
} from '../../../../../../app.constants';
import {ResizeObserverHelper} from '../../../../../../shared/helpers/resize-observer.helper';
import * as commonHelpers from '../../../../../../shared/helpers/common.helpers';
import {EditableCellApi} from './types/editable-cell-api';
import {Router, NavigationEnd} from '@angular/router';
import {takeUntil, filter, debounceTime} from 'rxjs/operators';
import {Subject} from 'rxjs';

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
    showAutopilotIcon: boolean;
    @Input()
    mode: EditableCellMode;
    @Input()
    containerElement: HTMLElement;
    @Input()
    @HostBinding('class.zem-editable-cell--metric')
    isMetric: boolean;
    @Output()
    modeChange = new EventEmitter<EditableCellMode>();
    @Output()
    placementChange = new EventEmitter<EditableCellPlacement>();
    @Output()
    componentReady = new EventEmitter<EditableCellApi>();

    @ViewChild(CdkPortal, {static: false})
    portal: CdkPortal;
    @ViewChild('portalContent', {static: false})
    portalContentElementRef: ElementRef;

    shouldRenderAsModal: boolean = false;
    hostElementOffsetTop: number;
    hostElementOffsetLeft: number;

    private portalHost: DomPortalHost;

    private onKeydownCallback: any;
    private onContainerElementScrollCallback: any;

    private resizeObserverDebouncer$: Subject<void> = new Subject<void>();
    private resizeObserverHelper: ResizeObserverHelper;

    private sidebarContainerContentElement: Element;
    private onSidebarContainerContentElementScrollCallback: any;

    private ngUnsubscribe$: Subject<void> = new Subject();

    constructor(
        @Inject(DOCUMENT) private document: Document,
        private componentFactoryResolver: ComponentFactoryResolver,
        private applicationRef: ApplicationRef,
        private injector: Injector,
        private hostElement: ElementRef,
        private renderer: Renderer2,
        private changeDetectorRef: ChangeDetectorRef,
        private router: Router
    ) {
        this.onSidebarContainerContentElementScrollCallback = this.switchToReadMode.bind(
            this
        );
        this.onKeydownCallback = this.onKeydown.bind(this);
        this.onContainerElementScrollCallback = this.switchToReadMode.bind(
            this
        );
        this.resizeObserverHelper = new ResizeObserverHelper(() => {
            this.resizeObserverDebouncer$.next();
        });
    }

    ngOnInit(): void {
        this.router.events
            .pipe(takeUntil(this.ngUnsubscribe$))
            .pipe(filter(event => event instanceof NavigationEnd))
            .subscribe(() => {
                this.modeChange.emit(EditableCellMode.READ);
            });
        this.resizeObserverDebouncer$
            .pipe(
                debounceTime(RESIZE_OBSERVER_DEBOUNCE_TIME),
                takeUntil(this.ngUnsubscribe$)
            )
            .subscribe(() => {
                if (
                    this.portalHost.hasAttached() &&
                    !this.shouldRenderAsModal
                ) {
                    this.switchToReadMode();
                }
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
        this.sidebarContainerContentElement = this.document.getElementById(
            'zem-sidebar-container__content'
        );
        this.componentReady.emit({
            expandAsModal: this.expandAsModal.bind(this),
        });
    }

    expandAsModal(): void {
        this.shouldRenderAsModal = true;
        this.placementChange.emit(EditableCellPlacement.MODAL);
        this.renderer.addClass(this.document.body, 'modal-open');
        this.changeDetectorRef.detectChanges();
    }

    ngOnDestroy(): void {
        this.detachHost();
        this.ngUnsubscribe$.next();
        this.ngUnsubscribe$.complete();
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
        this.placementChange.emit(EditableCellPlacement.IN_LINE);
        this.hostElementOffsetTop = hostElementOffset.topOffset;
        this.hostElementOffsetLeft = hostElementOffset.leftOffset;
        this.portalHost.attach(this.portal);

        if (commonHelpers.isDefined(this.sidebarContainerContentElement)) {
            this.sidebarContainerContentElement.addEventListener(
                'scroll',
                this.onSidebarContainerContentElementScrollCallback
            );
        }
        window.addEventListener('keydown', this.onKeydownCallback);
        this.containerElement.addEventListener(
            'scroll',
            this.onContainerElementScrollCallback
        );
        this.resizeObserverHelper.observe(this.containerElement);

        setTimeout(() => {
            this.shouldRenderAsModal = this.isPortalContentOverflowingContainer(
                this.hostElementOffsetLeft,
                this.portalContentElementRef,
                this.containerElement
            );
            if (this.shouldRenderAsModal) {
                this.placementChange.emit(EditableCellPlacement.MODAL);
                this.renderer.addClass(this.document.body, 'modal-open');
                this.changeDetectorRef.detectChanges();
            }
        });
    }

    private detachHost(): void {
        if (this.portalHost.hasAttached()) {
            this.portalHost.detach();

            if (commonHelpers.isDefined(this.sidebarContainerContentElement)) {
                this.sidebarContainerContentElement.removeEventListener(
                    'scroll',
                    this.onSidebarContainerContentElementScrollCallback
                );
            }
            window.removeEventListener('keydown', this.onKeydownCallback);
            this.containerElement.removeEventListener(
                'scroll',
                this.onContainerElementScrollCallback
            );
            this.resizeObserverHelper.unobserve(this.containerElement);
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
