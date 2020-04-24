import {SimpleChange, ElementRef, Renderer2} from '@angular/core';
import {InternalFeatureDirective} from './internal-feature.directive';

describe('InternalFeatureDirective', () => {
    let elementRefStub: ElementRef;
    let rendererSpy: jasmine.SpyObj<Renderer2>;
    let directive: InternalFeatureDirective;

    beforeEach(() => {
        elementRefStub = {nativeElement: jasmine.any(Object)};
        rendererSpy = jasmine.createSpyObj('Renderer2', [
            'addClass',
            'removeClass',
            'createElement',
            'appendChild',
            'removeChild',
        ]);
        rendererSpy.createElement.and.returnValue({});
        directive = new InternalFeatureDirective(elementRefStub, rendererSpy);
    });

    it('should add internal feature indicator element to host element on init when zemInternalFeature input has no value', () => {
        directive.ngOnInit();
        expect(rendererSpy.addClass).toHaveBeenCalledWith(
            elementRefStub.nativeElement,
            'zem-internal-feature'
        );
        expect(rendererSpy.appendChild).toHaveBeenCalledWith(
            elementRefStub.nativeElement,
            {
                className: 'zem-internal-feature__indicator',
            }
        );
    });

    it('should add internal feature indicator element to host element on input change when zemInternalFeature input is true', () => {
        directive.isInternal = true;
        directive.ngOnChanges({
            zemInternalFeature: new SimpleChange(null, true, false),
        });
        expect(rendererSpy.addClass).toHaveBeenCalledWith(
            elementRefStub.nativeElement,
            'zem-internal-feature'
        );
        expect(rendererSpy.appendChild).toHaveBeenCalledWith(
            elementRefStub.nativeElement,
            {
                className: 'zem-internal-feature__indicator',
            }
        );
    });

    it('should not remove internal feature indicator element from host element if it does not exist', () => {
        directive.isInternal = false;
        directive.ngOnChanges({
            zemInternalFeature: new SimpleChange(null, false, false),
        });
        expect(rendererSpy.removeClass).toHaveBeenCalledWith(
            elementRefStub.nativeElement,
            'zem-internal-feature'
        );
        expect(rendererSpy.removeChild).not.toHaveBeenCalled();
    });

    it('should remove internal feature indicator element from host element on input change when zemInternalFeature input is false', () => {
        directive.isInternal = true;
        directive.ngOnChanges({
            zemInternalFeature: new SimpleChange(null, true, false),
        });

        directive.isInternal = false;
        directive.ngOnChanges({
            zemInternalFeature: new SimpleChange(null, false, false),
        });
        expect(rendererSpy.removeClass).toHaveBeenCalledWith(
            elementRefStub.nativeElement,
            'zem-internal-feature'
        );
        expect(rendererSpy.removeChild).toHaveBeenCalledWith(
            elementRefStub.nativeElement,
            {
                className: 'zem-internal-feature__indicator',
            }
        );
    });
});
