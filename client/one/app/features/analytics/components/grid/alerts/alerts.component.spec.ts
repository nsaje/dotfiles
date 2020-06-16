import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {AlertsComponent} from './alerts.component';
import {SharedModule} from '../../../../../shared/shared.module';
import {Alert} from '../../../../../core/alerts/types/alert';
import {AlertType} from '../../../../../app.constants';
import {SimpleChange} from '@angular/core';
import {AlertStyleClass} from '../../../../../shared/components/alert/alert.component.constants';

describe('AlertsComponent', () => {
    let component: AlertsComponent;
    let fixture: ComponentFixture<AlertsComponent>;
    const mockedAlerts: Alert[] = [
        {
            type: AlertType.DANGER,
            message: 'Danger alert',
            isClosable: false,
        },
        {
            type: AlertType.SUCCESS,
            message: 'Success alert',
            isClosable: false,
        },
    ];

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [AlertsComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(AlertsComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly format alerts data on change', () => {
        component.alerts = mockedAlerts;
        component.ngOnChanges({
            alerts: new SimpleChange(null, mockedAlerts, false),
        });
        expect(component.formattedAlerts).toEqual([
            {
                styleClass: AlertStyleClass.Error,
                alert: mockedAlerts[0],
            },
            {
                styleClass: AlertStyleClass.Success,
                alert: mockedAlerts[1],
            },
        ]);
    });
});
