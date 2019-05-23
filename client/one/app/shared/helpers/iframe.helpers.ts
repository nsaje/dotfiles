import * as commonHelpers from './common.helpers';

const IFRAME_BODY_STYLE = '<style>body{margin: 0px; overflow: hidden;}</style>';

export function renderContentInIframe(
    iframe: HTMLElement,
    content: string
): void {
    if (!commonHelpers.isDefined(iframe)) {
        return;
    }

    const iframeWindow = (iframe as any).contentWindow || iframe;
    const iframeDocument =
        (iframe as any).contentDocument || (iframeWindow as any).document;
    if (commonHelpers.isDefined(iframeDocument)) {
        iframeDocument.open();
        iframeDocument.write(IFRAME_BODY_STYLE);
        iframeDocument.write(content || '');
        iframeDocument.close();
    }
}
