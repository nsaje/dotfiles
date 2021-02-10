const COLORS_COUNT = 64; // Number of colors in colors.less
const RANDOM_SEED = 13;

export function getTagColorCode(tag: string): number {
    return (
        ([...tag]
            .map(x => x.charCodeAt(0))
            .reduce(
                (prev: number, next: number) => prev * RANDOM_SEED + next,
                0
            ) %
            COLORS_COUNT) +
        1
    );
}
