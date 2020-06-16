import {TestBed, ComponentFixture} from '@angular/core/testing';
import {AlertComponent} from './alert.component';

describe('AlertComponent', () => {
    let component: AlertComponent;
    let fixture: ComponentFixture<AlertComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [AlertComponent],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(AlertComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
