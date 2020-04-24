import {ElementRef, Renderer2} from '@angular/core';
import {NewFeatureDirective} from './new-feature.directive';

describe('NewFeatureDirective', () => {
    let elementRefStub: ElementRef;
    let rendererSpy: jasmine.SpyObj<Renderer2>;
    let directive: NewFeatureDirective;

    beforeEach(() => {
        elementRefStub = {nativeElement: jasmine.any(Object)};
        rendererSpy = jasmine.createSpyObj('Renderer2', [
            'createElement',
            'appendChild',
            'removeChild',
        ]);
        rendererSpy.createElement.and.returnValue({});
        directive = new NewFeatureDirective(elementRefStub, rendererSpy);
    });

    it('should add new feature indicator element to host element on init when zemNewFeature input has no value', () => {
        directive.zemNewFeature = true;
        directive.ngOnChanges();
        expect(rendererSpy.appendChild).toHaveBeenCalledWith(
            elementRefStub.nativeElement,
            {
                className: 'zem-new-feature__text',
                innerText: 'NEW',
            }
        );
    });

    it('should add new feature indicator element to host element on input change when zemNewFeature input is true', () => {
        directive.zemNewFeature = true;
        directive.ngOnChanges();
        expect(rendererSpy.appendChild).toHaveBeenCalledWith(
            elementRefStub.nativeElement,
            {
                className: 'zem-new-feature__text',
                innerText: 'NEW',
            }
        );
    });

    it('should not remove new feature indicator element from host element if it does not exist', () => {
        directive.zemNewFeature = false;
        directive.ngOnChanges();
        expect(rendererSpy.appendChild).not.toHaveBeenCalled();
        expect(rendererSpy.removeChild).not.toHaveBeenCalled();
    });

    it('should remove new feature indicator element from host element on input change when zemNewFeature input is false', () => {
        directive.zemNewFeature = true;
        directive.ngOnChanges();

        directive.zemNewFeature = false;
        directive.ngOnChanges();
        expect(rendererSpy.removeChild).toHaveBeenCalledWith(
            jasmine.any(Object),
            {className: 'zem-new-feature__text', innerText: 'NEW'}
        );
    });
});
