import * as creativesManagerHelpers from './creatives-manager.helpers';
import {CREATIVES_MANAGER_CONFIG} from '../creatives-manager.config';

describe('CreativesManagerHelpers', () => {
    it('should correctly return iframe src for empty content', () => {
        const iframeSrc = creativesManagerHelpers.getPreviewIframeSrc(
            CREATIVES_MANAGER_CONFIG.previewIframeSrcPrefix,
            ''
        );
        const expected = CREATIVES_MANAGER_CONFIG.previewIframeSrcPrefix;

        expect(iframeSrc).toEqual(expected);
    });

    it('should correctly return iframe src for content', () => {
        const srcContent = '<span>Hello world</span>';
        const iframeSrc = creativesManagerHelpers.getPreviewIframeSrc(
            CREATIVES_MANAGER_CONFIG.previewIframeSrcPrefix,
            srcContent
        );
        const expected = `${
            CREATIVES_MANAGER_CONFIG.previewIframeSrcPrefix
        }${srcContent}`;

        expect(iframeSrc).toEqual(expected);
    });
});
