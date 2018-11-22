export function getPreviewIframeSrc(
    srcPrefix: String,
    srcContent: String
): String {
    if (!srcContent) {
        return srcPrefix;
    }
    return `${srcPrefix}${srcContent}`;
}
