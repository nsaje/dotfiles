import {ElementRef, OnChanges, Renderer2} from '@angular/core';
import {TagDirective} from './tag.directive';

class TestTagDirective extends TagDirective implements OnChanges {
    zemTestTag: boolean = true;
    zemTestTagClass: string = '';

    constructor(
        protected elementRef: ElementRef,
        protected renderer: Renderer2
    ) {
        super(elementRef, renderer);
        this.tagText = 'TEST';
        this.tagTextClass = 'zem-test-tag__text';
    }

    ngOnChanges(): void {
        this.isTagDisplayed = this.zemTestTag;
        this.tagClass = this.zemTestTagClass;
        super.updateDisplay();
    }
}

describe('TestTagDirective', () => {
    let elementRefStub: ElementRef;
    let rendererSpy: jasmine.SpyObj<Renderer2>;
    let directive: TestTagDirective;

    beforeEach(() => {
        elementRefStub = {nativeElement: jasmine.any(Object)};
        rendererSpy = jasmine.createSpyObj('Renderer2', [
            'createElement',
            'appendChild',
            'removeChild',
        ]);
        rendererSpy.createElement.and.returnValue({});
        directive = new TestTagDirective(elementRefStub, rendererSpy);
    });

    it('should add tag to host element on init when zemTestTag input has no value', () => {
        directive.zemTestTag = true;
        directive.ngOnChanges();
        expect(rendererSpy.appendChild).toHaveBeenCalledWith(
            elementRefStub.nativeElement,
            {
                className: 'zem-tag__text zem-test-tag__text',
                innerText: 'TEST',
            }
        );
    });

    it('should add tag to host element on input change when zemTestTag input is true', () => {
        directive.zemTestTag = true;
        directive.ngOnChanges();
        expect(rendererSpy.appendChild).toHaveBeenCalledWith(
            elementRefStub.nativeElement,
            {
                className: 'zem-tag__text zem-test-tag__text',
                innerText: 'TEST',
            }
        );
    });

    it('should not remove tag from host element if it does not exist', () => {
        directive.zemTestTag = false;
        directive.ngOnChanges();
        expect(rendererSpy.appendChild).not.toHaveBeenCalled();
        expect(rendererSpy.removeChild).not.toHaveBeenCalled();
    });

    it('should remove tag from host element on input change when zemTestTag input is false', () => {
        directive.zemTestTag = true;
        directive.ngOnChanges();

        directive.zemTestTag = false;
        directive.ngOnChanges();
        expect(rendererSpy.removeChild).toHaveBeenCalledWith(
            jasmine.any(Object),
            {className: 'zem-tag__text zem-test-tag__text', innerText: 'TEST'}
        );
    });
});
