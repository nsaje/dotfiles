import {TestBed, ComponentFixture} from '@angular/core/testing';
import {FormsModule} from '@angular/forms';
import {SharedModule} from '../../../../shared/shared.module';
import {OperatingSystemComponent} from './operating-system.component';
import {TargetOperatingSystem} from '../../../../core/entities/types/common/target-operating-system';
import {ChangeEvent} from '../../../../shared/types/change-event';
import {PlatformIcon} from './operating-system.constants';

describe('OperatingSystemComponent', () => {
    let component: OperatingSystemComponent;
    let fixture: ComponentFixture<OperatingSystemComponent>;

    function setUpAndStartSpying(initialState: TargetOperatingSystem) {
        component.os = initialState;
        component.ngOnChanges();

        spyOn(component.osChange, 'emit');
        spyOn(component.osDelete, 'emit');
    }

    function expectChangeEvent(
        changeEvent: ChangeEvent<TargetOperatingSystem>
    ) {
        expect(component.osChange.emit).toHaveBeenCalled();
        expect(component.osChange.emit).toHaveBeenCalledWith(changeEvent);
        expect(component.osDelete.emit).not.toHaveBeenCalled();
    }

    beforeEach(() => {
        TestBed.configureTestingModule({
            declarations: [OperatingSystemComponent],
            imports: [FormsModule, SharedModule],
        });
    });

    beforeEach(() => {
        fixture = TestBed.createComponent(OperatingSystemComponent);
        component = fixture.componentInstance;
    });

    it('should be correctly initialized', () => {
        expect(component).toBeDefined();
    });

    it('should correctly set the selected OS from input', () => {
        component.os = {
            name: 'WINDOWS',
            version: {min: 'WINDOWS_VISTA', max: 'WINDOWS_10'},
        };
        component.ngOnChanges();
        expect(component.formattedOs.name).toEqual('WINDOWS');
        expect(component.minVersion.name).toEqual('WINDOWS_VISTA');
        expect(component.maxVersion.name).toEqual('WINDOWS_10');
        expect(component.platformIcon).toEqual(PlatformIcon.DESKTOP);

        component.os = {
            name: 'ANDROID',
            version: {min: 'ANDROID_4_0', max: 'ANDROID_5_0'},
        };
        component.ngOnChanges();
        expect(component.formattedOs.name).toEqual('ANDROID');
        expect(component.minVersion.name).toEqual('ANDROID_4_0');
        expect(component.maxVersion.name).toEqual('ANDROID_5_0');
        expect(component.platformIcon).toEqual(PlatformIcon.TABLET_MOBILE);
    });

    it('should allow undefined min version of an OS', () => {
        component.os = {
            name: 'WINDOWS',
            version: {min: null, max: 'WINDOWS_10'},
        };
        component.ngOnChanges();
        expect(component.minVersion).not.toBeDefined();
        expect(component.maxVersion).toBeDefined();
    });

    it('should allow undefined max version of an OS', () => {
        component.os = {
            name: 'WINDOWS',
            version: {min: 'WINDOWS_VISTA', max: null},
        };
        component.ngOnChanges();
        expect(component.minVersion).toBeDefined();
        expect(component.maxVersion).not.toBeDefined();
    });

    it('should ignore non-existent OS versions', () => {
        component.os = {
            name: 'WINDOWS',
            version: {min: 'WINDOWS_96', max: 'WINDOWS_97'},
        };
        component.ngOnChanges();
        expect(component.formattedOs.name).toEqual('WINDOWS');
        expect(component.minVersion).not.toBeDefined();
        expect(component.maxVersion).not.toBeDefined();
    });

    it('should throw an error for non-existent OS types', () => {
        const os = {
            name: 'WINUX',
            version: {min: 'WINUX_VISTA', max: 'WINUX_10'},
        };

        expect(() => {
            component.os = os;
            component.ngOnChanges();
        }).toThrowError();
    });

    it('should support an OS without any defined versions', () => {
        component.os = {name: 'LINUX', version: {min: null, max: null}};
        component.ngOnChanges();
        expect(component.minVersion).not.toBeDefined();
        expect(component.maxVersion).not.toBeDefined();
    });

    it("should ignore any versions specified for an OS that doesn't have any", () => {
        component.os = {
            name: 'LINUX',
            version: {min: 'UBUNTU_18.04', max: 'UBUNTU_19.10'},
        };
        component.ngOnChanges();
        expect(component.minVersion).not.toBeDefined();
        expect(component.maxVersion).not.toBeDefined();
    });

    it('should allow changing of min OS version', () => {
        setUpAndStartSpying({
            name: 'WINDOWS',
            version: {min: 'WINDOWS_VISTA', max: 'WINDOWS_7'},
        });
        component.onVersionChanged('WINDOWS_XP', 'min');
        expectChangeEvent({
            target: component.os,
            changes: {version: {min: 'WINDOWS_XP', max: 'WINDOWS_7'}},
        });
    });

    it('should allow deleting of min OS version', () => {
        setUpAndStartSpying({
            name: 'WINDOWS',
            version: {min: 'WINDOWS_VISTA', max: 'WINDOWS_7'},
        });
        component.onVersionChanged(null, 'min');
        expectChangeEvent({
            target: component.os,
            changes: {version: {min: undefined, max: 'WINDOWS_7'}},
        });
    });

    it('should allow changing of max OS version', () => {
        setUpAndStartSpying({
            name: 'WINDOWS',
            version: {min: 'WINDOWS_VISTA', max: 'WINDOWS_7'},
        });
        component.onVersionChanged('WINDOWS_10', 'max');
        expectChangeEvent({
            target: component.os,
            changes: {version: {min: 'WINDOWS_VISTA', max: 'WINDOWS_10'}},
        });
    });

    it('should allow deleting of max OS version', () => {
        setUpAndStartSpying({
            name: 'WINDOWS',
            version: {min: 'WINDOWS_VISTA', max: 'WINDOWS_7'},
        });
        component.onVersionChanged(null, 'max');
        expectChangeEvent({
            target: component.os,
            changes: {version: {min: 'WINDOWS_VISTA', max: undefined}},
        });
    });

    it('should support OS deletion', () => {
        setUpAndStartSpying({
            name: 'WINDOWS',
            version: {min: 'WINDOWS_VISTA', max: 'WINDOWS_7'},
        });
        component.onOsDeleted();
        expect(component.osChange.emit).not.toHaveBeenCalled();
        expect(component.osDelete.emit).toHaveBeenCalled();
    });
});
