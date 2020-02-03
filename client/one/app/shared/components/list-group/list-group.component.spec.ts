import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {ListGroupComponent} from './list-group.component';

describe('ListGroupComponent', () => {
    let component: ListGroupComponent;
    let fixture: ComponentFixture<ListGroupComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [ListGroupComponent],
            imports: [FormsModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(ListGroupComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});