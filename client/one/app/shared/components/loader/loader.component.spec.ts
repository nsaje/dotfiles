import {TestBed, ComponentFixture} from '@angular/core/testing';
import {LoaderComponent} from './loader.component';

describe('LoaderComponent', () => {
    let component: LoaderComponent;
    let fixture: ComponentFixture<LoaderComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [LoaderComponent],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(LoaderComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
