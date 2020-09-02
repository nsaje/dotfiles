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

    it('should supply inputs to super class on changes', () => {
        expect(directive.isTagDisplayed).toBeTrue();
        expect(directive.tagClass).toEqual('');

        directive.zemNewFeature = false;
        directive.zemNewFeatureClass = 'xxx';
        directive.ngOnChanges();
        expect(directive.isTagDisplayed).toBeFalse();
        expect(directive.tagClass.split(' ').includes('xxx')).toBeTrue();

        directive.zemNewFeature = true;
        directive.zemNewFeatureClass = 'test';
        directive.ngOnChanges();
        expect(directive.isTagDisplayed).toBeTrue();
        expect(directive.tagClass.split(' ').includes('test')).toBeTrue();
    });
});
