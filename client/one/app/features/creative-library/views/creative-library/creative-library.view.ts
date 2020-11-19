import './creative-library.view.less';

import {Component, ChangeDetectionStrategy, HostBinding} from '@angular/core';

@Component({
    selector: 'zem-creative-library-view',
    templateUrl: './creative-library.view.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CreativeLibraryView {
    @HostBinding('class')
    cssClass = 'zem-creative-library-view';
}
