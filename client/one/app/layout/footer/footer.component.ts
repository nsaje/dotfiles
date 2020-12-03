import './footer.component.less';

import {OnInit, Component, ChangeDetectionStrategy} from '@angular/core';
import * as commonHelpers from '../../shared/helpers/common.helpers';
import {
    DEFAULT_COPYRIGHT_HOLDER,
    DEFAULT_COPYRIGHT_HOLDER_URL,
    DEFAULT_TERMS_OF_SERVICE_URL,
} from './footer.component.constants';

@Component({
    selector: 'zem-footer',
    templateUrl: './footer.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class FooterComponent implements OnInit {
    termsOfServiceUrl: string;
    copyrightHolder: string;
    copyrightHolderUrl: string;

    ngOnInit(): void {
        this.termsOfServiceUrl = commonHelpers.getValueOrDefault(
            (window as any).zOne.whitelabel.termsOfServiceUrl,
            DEFAULT_TERMS_OF_SERVICE_URL
        );
        this.copyrightHolder = commonHelpers.getValueOrDefault(
            (window as any).zOne.whitelabel.copyrightHolder,
            DEFAULT_COPYRIGHT_HOLDER
        );
        this.copyrightHolderUrl = commonHelpers.getValueOrDefault(
            (window as any).zOne.whitelabel.copyrightHolderUrl,
            DEFAULT_COPYRIGHT_HOLDER_URL
        );
    }
}
