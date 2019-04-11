import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {HacksComponent} from './hacks.component';

describe('HacksComponent', () => {
    let component: HacksComponent;
    let fixture: ComponentFixture<HacksComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [HacksComponent],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(HacksComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
