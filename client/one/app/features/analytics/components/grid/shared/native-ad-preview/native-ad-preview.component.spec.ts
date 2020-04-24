import {TestBed, ComponentFixture} from '@angular/core/testing';
import {NativeAdPreviewComponent} from './native-ad-preview.component';

describe('DisplayAdPreviewComponent', () => {
    let component: NativeAdPreviewComponent;
    let fixture: ComponentFixture<NativeAdPreviewComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [NativeAdPreviewComponent],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(NativeAdPreviewComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
