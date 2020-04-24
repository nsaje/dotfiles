import {TestBed, ComponentFixture} from '@angular/core/testing';
import {DisplayAdPreviewComponent} from './display-ad-preview.component';

describe('DisplayAdPreviewComponent', () => {
    let component: DisplayAdPreviewComponent;
    let fixture: ComponentFixture<DisplayAdPreviewComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [DisplayAdPreviewComponent],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(DisplayAdPreviewComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
