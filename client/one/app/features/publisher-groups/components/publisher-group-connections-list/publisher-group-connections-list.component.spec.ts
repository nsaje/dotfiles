import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {PublisherGroupConnectionsListComponent} from './publisher-group-connections-list.component';

describe('PublisherGroupConnectionsListComponent', () => {
    let component: PublisherGroupConnectionsListComponent;
    let fixture: ComponentFixture<PublisherGroupConnectionsListComponent>;

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [PublisherGroupConnectionsListComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(
            PublisherGroupConnectionsListComponent
        );
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });
});
