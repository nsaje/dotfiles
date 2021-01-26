import {TestBed, ComponentFixture} from '@angular/core/testing';
import {LoaderComponent} from '../loader/loader.component';
import {ButtonComponent} from './button.component';

describe('ButtonComponent', () => {
    let component: ButtonComponent;
    let fixture: ComponentFixture<ButtonComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [ButtonComponent, LoaderComponent],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ButtonComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
