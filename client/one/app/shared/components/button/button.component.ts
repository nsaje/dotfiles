import './button.component.less';

import {
    Component,
    ChangeDetectionStrategy,
    EventEmitter,
    Output,
    Input,
    OnChanges,
    HostBinding,
    ContentChild,
    TemplateRef,
} from '@angular/core';
import * as commonHelpers from '../../helpers/common.helpers';

@Component({
    selector: 'zem-button',
    templateUrl: './button.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ButtonComponent implements OnChanges {
    @Input()
    isDisabled: boolean = false;
    @Input()
    isHighlighted: boolean = false;
    @Input()
    isOutlined: boolean = false;
    @Input()
    isSmall: boolean = false;
    @Input()
    set isFullWidth(value: boolean) {
        this.fullWidthClass = value;
    }
    @Input()
    isDanger: boolean = false;
    @Input()
    isLoading: boolean = false;
    @Input()
    icon: string;
    @Input()
    isIconOnly: boolean = false;

    @ContentChild('loaderTemplate', {read: TemplateRef, static: false})
    loaderTemplate: TemplateRef<any>;

    @HostBinding('class.zem-button__button--full-width') fullWidthClass = false;

    buttonClass: {[key: string]: boolean} = {
        'zem-button__button': true,
    };
    loaderClass: {[key: string]: boolean} = {};

    ngOnChanges() {
        this.buttonClass = {
            'zem-button__button': true,
            'zem-button__button--highlighted': this.isHighlighted,
            'zem-button__button--outlined': this.isOutlined,
            'zem-button__button--small': this.isSmall,
            'zem-button__button--danger': this.isDanger,
            'zem-button__button--with-icon':
                commonHelpers.isDefined(this.icon) || this.isLoading,
            'zem-button__button--icon-only': this.isIconOnly,
            [`zem-button__button--${this.icon}-icon`]:
                commonHelpers.isDefined(this.icon) && !this.isLoading,
        };
        this.loaderClass = {
            'zem-button__button-loader': true,
            'zem-button__button-loader--small': this.isSmall,
            'zem-loader': true,
            'zem-loader--smaller': !this.isSmall,
            'zem-loader--smallest': this.isSmall,
            'zem-loader--secondary': !(this.isHighlighted || this.isDanger),
            'zem-loader--white': this.isHighlighted || this.isDanger,
        };
    }
}
