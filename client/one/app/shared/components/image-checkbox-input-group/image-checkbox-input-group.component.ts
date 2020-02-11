import './image-checkbox-input-group.component.less';
import {
    ChangeDetectionStrategy,
    Component,
    ContentChild,
    Input,
    OnChanges,
    TemplateRef,
} from '@angular/core';
import {ImageCheckboxInputItem} from '../image-checkbox-input/types/image-checkbox-input-item';
import {ImageCheckboxInputGroupItem} from './types/image-checkbox-input-group-item';

@Component({
    selector: 'zem-image-checkbox-input-group',
    templateUrl: './image-checkbox-input-group.component.html',
    changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ImageCheckboxInputGroupComponent implements OnChanges {
    @Input()
    options: ImageCheckboxInputGroupItem[] = [];
    @Input()
    values: string[] = [];

    @ContentChild('imageCheckboxTemplate', {read: TemplateRef, static: false})
    imageCheckboxTemplate: TemplateRef<any>;

    formattedOptions: ImageCheckboxInputItem[] = [];

    ngOnChanges() {
        this.formattedOptions = this.getFormattedOptions(this.options);
    }

    private getFormattedOptions(
        options: ImageCheckboxInputGroupItem[]
    ): ImageCheckboxInputItem[] {
        return (options || []).map(option => {
            return {
                ...option,
                checked: this.values.includes(option.value),
            };
        });
    }
}
